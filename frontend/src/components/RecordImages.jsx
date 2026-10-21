import { useEffect, useRef, useState } from "react";

import { deleteRecordImage, fetchRecordImages, imageUrl, uploadRecordImages } from "../services/api";

const CATEGORIES = ["tomato", "plant", "leaf", "other"];

export default function RecordImages({ recordId }) {
  const [images, setImages] = useState([]);
  const [category, setCategory] = useState("tomato");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const fileInput = useRef(null);

  useEffect(() => {
    let cancelled = false;
    fetchRecordImages(recordId)
      .then((result) => {
        if (!cancelled) setImages(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [recordId]);

  const handleUpload = async (event) => {
    const files = event.target.files;
    if (!files?.length) return;

    setBusy(true);
    setError(null);
    try {
      const uploaded = await uploadRecordImages(recordId, files, category);
      setImages((current) => [...current, ...uploaded]);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  };

  const handleDelete = async (image) => {
    if (!window.confirm("Delete this image?")) return;

    try {
      setError(null);
      await deleteRecordImage(image.id);
      setImages((current) => current.filter((item) => item.id !== image.id));
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="record-images">
      <div className="record-images-grid">
        {images.map((image) => (
          <figure key={image.id}>
            <a href={imageUrl(image)} target="_blank" rel="noreferrer">
              <img src={imageUrl(image)} alt={image.caption || image.category} loading="lazy" />
            </a>
            <figcaption>
              {image.category}
              <button type="button" onClick={() => handleDelete(image)} aria-label="Delete image">
                ×
              </button>
            </figcaption>
          </figure>
        ))}
      </div>
      <div className="record-images-upload">
        <select value={category} onChange={(event) => setCategory(event.target.value)}>
          {CATEGORIES.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
        <input
          ref={fileInput}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          capture="environment"
          multiple
          disabled={busy}
          onChange={handleUpload}
        />
      </div>
      {error ? <p className="form-error">{error}</p> : null}
    </div>
  );
}
