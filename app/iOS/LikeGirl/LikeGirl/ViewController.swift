//
//  ViewController.swift
//  LikeGirl
//
//  Created by SHUAI on 2017/7/13.
//  Copyright © 2017年 SHUAI. All rights reserved.
//

import UIKit

class ViewController: UIViewController, UIImagePickerControllerDelegate, UIPopoverControllerDelegate, UINavigationControllerDelegate, UITableViewDataSource, UITableViewDelegate {
    
    var picker: UIImagePickerController? = UIImagePickerController()
    
    @IBOutlet weak var imageView: UIImageView!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        picker?.delegate = self
    }
    
    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
    }
    
    // Open Gallery button click
    @IBAction func OpenGallery(sender: AnyObject) {
        openGallary()
    }
    
    // Take Photo button click
    @IBAction func TakePhoto(sender: AnyObject) {
        openCamera()
    }
    
    func openGallary() {
        picker!.allowsEditing = false
        picker!.sourceType = UIImagePickerControllerSourceType.photoLibrary
        present(picker!, animated: true, completion: nil)
    }
    
    func openCamera() {
        if (UIImagePickerController.isSourceTypeAvailable(UIImagePickerControllerSourceType.camera)) {
            picker!.allowsEditing = false
            picker!.sourceType = UIImagePickerControllerSourceType.camera
            picker!.cameraCaptureMode = .photo            
            present(picker!, animated: true, completion: nil)
        } else {
            showAlert(title: "Camera Not Found", message: "This device has no Camera")
        }
    }
    
    func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
        dismiss(animated: true, completion: nil)
    }
    
    func imagePickerController(_ picker: UIImagePickerController, didFinishPickingMediaWithInfo info: [String : Any]) {
        let chosenImage = info[UIImagePickerControllerOriginalImage] as! UIImage
        imageView.contentMode = .scaleAspectFit
        imageView.image = chosenImage
        dismiss(animated: true, completion: nil)
        
        if (picker.sourceType == .camera) {
            // UIImageWriteToSavedPhotosAlbum(chosenImage, self, #selector(ViewController.image(_: didFinishSavingWithError:contextInfo:)), nil)
            UIImageWriteToSavedPhotosAlbum(chosenImage, nil, nil, nil)
        }
        
        tableData = []
        tableActress.reloadData()
        notFoundLabel.isHidden = true
        
        if Reachability.shared.isConnectedToNetwork() {
            postImage()
        } else {
            showAlert(title: "Internet Not Connected", message: "Internet Connection is Required")
        }
    }
    
    /* func image(_ image: UIImage, didFinishSavingWithError error: Error?, contextInfo: UnsafeRawPointer) {
        if let error = error {
            // we got back an error!
            let alert = UIAlertController(title: "Save error", message: error.localizedDescription, preferredStyle: .alert)
            alert.addAction(UIAlertAction(title: "OK", style: .default))
            present(alert, animated: true)
        } else {
            let alert = UIAlertController(title: "Saved!", message: "Your altered image has been saved to your photos.", preferredStyle: .alert)
            alert.addAction(UIAlertAction(title: "OK", style: .default))
            present(alert, animated: true)
        }
    } */
    
    let activityIndicator: UIActivityIndicatorView = UIActivityIndicatorView()
    
    var tableData: [[String: Any]] = []
    var filename: String?
    
    @IBOutlet weak var tableActress: UITableView!
    @IBOutlet weak var notFoundLabel: UILabel!
    
    public func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return tableData.count
    }
    
    public func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cellActress = tableActress.dequeueReusableCell(withIdentifier: "cellActress", for: indexPath) as! ActressTableViewCell
        let row = indexPath.row
        
        cellActress.tag = row
        cellActress.didPressFeedbackButton = { row, isLike in
            if Reachability.shared.isConnectedToNetwork() {
                cellActress.hiddenFeedbackAndShowThanks()
                self.postFeedback(row: row, isLike: isLike)
            } else {
                self.showAlert(title: "Internet Not Connected", message: "Internet Connection is Required")
            }
        }
        
        let img = tableData[row]["Img"] as! String
        let imgUrl = URL(string: img)
        let imageData = try? Data(contentsOf: imgUrl!)
        cellActress.actressImage.image = UIImage(data: imageData!)
        cellActress.nameLabel.text = tableData[row]["Name"] as? String
        cellActress.similarityLabel.text = (tableData[row]["Similarity"] as? String)! + "%"
        
        cellActress.unlikeButton.isHidden = false
        cellActress.likeButton.isHidden = false
        cellActress.thanksLabel.isHidden = true
        
        return cellActress
    }
    
    /* public func tableView(_ tableView: UITableView, editActionsForRowAt indexPath: IndexPath) -> [UITableViewRowAction]? {
        let cellActress = self.tableActress.dequeueReusableCell(withIdentifier: "cellActress", for: indexPath) as! ActressTableViewCell
        cellActress.tag = indexPath.row
        
        let likeAction = UITableViewRowAction(style: .default, title: "O\nLIKE") { (rowAction, indexPath) in
            self.postFeedback(cell: cellActress, isLike: true)
        }
        likeAction.backgroundColor = .blue
        
        let unlikeAction = UITableViewRowAction(style: .default, title: "X\nUNLIKE") { (rowAction, indexPath) in
            self.postFeedback(cell: cellActress, isLike: false)
        }
        unlikeAction.backgroundColor = .gray
        
        return [likeAction, unlikeAction]
    } */
    
    func postImage() {
        var request  = URLRequest(url: URL(string: "https://like-av.xyz/api/upload")!)
        request.httpMethod = "POST"
        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.httpBody = createRequestBodyWith(parameters: nil, boundary: boundary)
        
        activityIndicator.center = view.center
        activityIndicator.hidesWhenStopped = true
        activityIndicator.activityIndicatorViewStyle = UIActivityIndicatorViewStyle.gray
        activityIndicator.transform = CGAffineTransform(scaleX: 2, y: 2)
        view.addSubview(activityIndicator)
        activityIndicator.startAnimating()
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            guard let data = data, error == nil else { // check for fundamental networking error
                // print("error=(error)")
                
                return
            }
            
            if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode != 200 { // check for http errors
                // print("statusCode should be 200, but is \(httpResponse.statusCode)")
                // print("response = \(httpResponse)")
                
                return
            }
            
            do {
                /* let parsedData = try JSONSerialization.jsonObject(with: data) as! [String: Any]
                let count = parsedData["Count"] as! Int
                
                self.filename = parsedData["File"] as? String
                self.tableData = count == 0 ? [] : parsedData["Data"] as! [[String: Any]]
                
                DispatchQueue.main.async() {
                    self.tableActress.reloadData()
                    self.activityIndicator.stopAnimating()
                } */
                
                
                let parsedData = try JSONSerialization.jsonObject(with: data) as! [String: Any]
                let count = parsedData["Count"] as! Int
                self.filename = parsedData["File"] as? String
                DispatchQueue.main.async() {
                    if (count == 0) {
                        self.notFoundLabel.isHidden = false
                        self.tableData = []
                    } else {
                        self.tableData = parsedData["Data"] as! [[String: Any]]
                    }
                    
                    self.tableActress.reloadData()
                    self.activityIndicator.stopAnimating()
                }
            } catch _ as NSError {
                // let error as NSError
                // print(error)
            }
        }.resume()
    }
    
    func createRequestBodyWith(parameters: [String: String]?, boundary: String) -> Data {
        let body = NSMutableData()
        
        if parameters != nil {
            for (key, value) in parameters! {
                body.appendString(string: "--\(boundary)\r\n")
                body.appendString(string: "Content-Disposition: form-data; name=\"\(key)\"\r\n\r\n")
                body.appendString(string: "\(value)\r\n")
            }
        }
        
        body.appendString(string: "--\(boundary)\r\n")
        
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd-HH-mm-ss"
        formatter.timeZone = TimeZone(identifier: "UTC")
        let filename = formatter.string(from: Date()) + ".jpg"
        // print(filename)
        body.appendString(string: "Content-Disposition: form-data; name=\"upload\"; filename=\"\(filename)\"\r\n")
        
        let mimetype = "image/jpg"
        body.appendString(string: "Content-Type: \(mimetype)\r\n\r\n")
        
        let imageData = UIImageJPEGRepresentation(imageView.image!, 0.8) // compression is 0(most)..1(least)
        body.append(imageData!)
        
        body.appendString(string: "\r\n")
        body.appendString(string: "--\(boundary)--\r\n")
        
        return body as Data
    }
    
    func postFeedback(row: Int, isLike: Bool) {
        var request  = URLRequest(url: URL(string: "https://like-av.xyz/api/feedback")!)
        request.httpMethod = "POST"
        
        let actress = tableData[row]
        let ox = isLike ? "like" : "unlike"
        let data = ["id": actress["Id"], "ox": ox, "file": filename]
        request.httpBody = try! JSONSerialization.data(withJSONObject: data)
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")
        URLSession.shared.dataTask(with: request) { data, response, error in
            if error != nil{
                // print("error=(error)")
                
                return
            }
        }.resume()
    }
    
    func showAlert(title: String, message: String) {
        let alert = UIAlertController(title: title, message: message, preferredStyle: .alert)
        let ok = UIAlertAction(title: "OK", style: .default, handler: nil)
        alert.addAction(ok)
        present(alert, animated: true, completion: nil)
    }
}

extension NSMutableData {
    func appendString(string: String) {
        let data = string.data(using: String.Encoding.utf8, allowLossyConversion: true)
        append(data!)
    }
}

