Page({
  data: {
    photoUrl: '',
    resultUrl: ''
  },
  takePhoto() {
    const ctx = wx.createCameraContext();
    ctx.takePhoto({
      quality: 'high',
      success: (res) => {
        this.setData({
          photoUrl: res.tempImagePath
        });
        this.uploadPhoto(res.tempImagePath);
      }
    });
  },
  uploadPhoto(imgPath) {
    wx.uploadFile({
      url: 'http://localhost:5000/api/detect',
      filePath: imgPath,
      name: 'file',
      success: (res) => {
        const data = JSON.parse(res.data);
        this.setData({
          resultUrl: data.result_image
        });
      }
    });
  }
});
