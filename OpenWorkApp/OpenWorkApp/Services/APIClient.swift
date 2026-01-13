import Foundation

class APIClient {
    private let baseURL: String
    private let session: URLSession
    
    init(baseURL: String = "http://127.0.0.1:8765") {
        self.baseURL = baseURL
        self.session = URLSession.shared
    }
    
    func healthCheck(completion: @escaping (Result<Bool, Error>) -> Void) {
        guard let url = URL(string: "\(baseURL)/health") else {
            completion(.failure(APIError.invalidURL))
            return
        }
        
        session.dataTask(with: url) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                completion(.failure(APIError.serverError))
                return
            }
            
            completion(.success(true))
        }.resume()
    }
    
    func createTask(
        task: String,
        allowedPaths: [String],
        model: String,
        apiKey: String,
        completion: @escaping (Result<TaskResponse, Error>) -> Void
    ) {
        guard let url = URL(string: "\(baseURL)/tasks") else {
            completion(.failure(APIError.invalidURL))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = [
            "task": task,
            "allowed_paths": allowedPaths,
            "model": model,
            "api_key": apiKey
        ]
        
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
        } catch {
            completion(.failure(error))
            return
        }
        
        session.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else {
                completion(.failure(APIError.noData))
                return
            }
            
            do {
                let taskResponse = try JSONDecoder().decode(TaskResponse.self, from: data)
                completion(.success(taskResponse))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
    
    func getTask(taskId: String, completion: @escaping (Result<TaskResponse, Error>) -> Void) {
        guard let url = URL(string: "\(baseURL)/tasks/\(taskId)") else {
            completion(.failure(APIError.invalidURL))
            return
        }
        
        session.dataTask(with: url) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else {
                completion(.failure(APIError.noData))
                return
            }
            
            do {
                let taskResponse = try JSONDecoder().decode(TaskResponse.self, from: data)
                completion(.success(taskResponse))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
    
    func listModels(completion: @escaping (Result<[String], Error>) -> Void) {
        guard let url = URL(string: "\(baseURL)/models") else {
            completion(.failure(APIError.invalidURL))
            return
        }
        
        session.dataTask(with: url) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else {
                completion(.failure(APIError.noData))
                return
            }
            
            do {
                if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let models = json["models"] as? [[String: Any]] {
                    let modelIds = models.compactMap { $0["id"] as? String }
                    completion(.success(modelIds))
                } else {
                    completion(.failure(APIError.parseError))
                }
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
}

enum APIError: Error, LocalizedError {
    case invalidURL
    case serverError
    case noData
    case parseError
    
    var errorDescription: String? {
        switch self {
        case .invalidURL: return "Invalid URL"
        case .serverError: return "Server error"
        case .noData: return "No data received"
        case .parseError: return "Failed to parse response"
        }
    }
}
