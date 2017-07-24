//
//  ActressTableViewCell.swift
//  LikeGirl
//
//  Created by SHUAI on 2017/7/16.
//  Copyright © 2017年 SHUAI. All rights reserved.
//

import UIKit

class ActressTableViewCell: UITableViewCell {

    @IBOutlet weak var actressImage: UIImageView!
    @IBOutlet weak var nameLabel: UILabel!
    @IBOutlet weak var similarityLabel: UILabel!
    @IBOutlet weak var unlikeButton: UIButton!
    @IBOutlet weak var likeButton: UIButton!
    @IBOutlet weak var thanksLabel: UILabel!

    var didPressFeedbackButton : ((Int, Bool) -> Void)?
    
    override func awakeFromNib() {
        super.awakeFromNib()
        // Initialization code
        
        actressImage.layer.cornerRadius = actressImage.frame.size.width / 2
        actressImage.clipsToBounds = true
    }

    override func setSelected(_ selected: Bool, animated: Bool) {
        super.setSelected(selected, animated: animated)

        // Configure the view for the selected state
    }

    @IBAction func unlikeAction(_ sender: AnyObject) {
        didPressFeedbackButton!(self.tag, false)
    }

    @IBAction func likeAction(_ sender: AnyObject) {
        didPressFeedbackButton!(self.tag, true)
    }
    
    public func hiddenFeedbackAndShowThanks() {
        unlikeButton.isHidden = true
        likeButton.isHidden = true
        thanksLabel.isHidden = false
    }
}
