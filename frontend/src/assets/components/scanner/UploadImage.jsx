import { useState } from "react"

export default function UploadImage() {

  const [image,setImage] = useState(null)

  function handleUpload(e){
    const file = e.target.files[0]
    setImage(URL.createObjectURL(file))
  }

  return(
    <div className="card">

      <h3>Upload Vehicle Image</h3>

      <input type="file" onChange={handleUpload} />

      {image && (
        <img
          src={image}
          className="preview"
        />
      )}

      <button className="btn">
        Scan Plate
      </button>

    </div>
  )
}