import { FormEvent, useEffect, useState } from "react";

import {
  createFileAsset,
  deleteFileAsset,
  fetchFileAssets,
  updateFileAsset
} from "../api/client";
import type { FileAsset } from "../types";

interface FileFormState {
  product_type: string;
  label: string;
  path: string;
  os_type: string;
  checksum: string;
}

const defaultForm = (): FileFormState => ({
  product_type: "vpn",
  label: "",
  path: "",
  os_type: "",
  checksum: ""
});

const FilesPage = () => {
  const [files, setFiles] = useState<FileAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<FileFormState>(defaultForm());
  const [editingId, setEditingId] = useState<number | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchFileAssets();
        setFiles(data);
        setError(null);
      } catch (err) {
        console.error(err);
        setError("Не удалось загрузить файлы");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    try {
      const payload = {
        product_type: form.product_type,
        label: form.label,
        path: form.path,
        os_type: form.os_type || null,
        checksum: form.checksum || null
      };
      const updated = editingId
        ? await updateFileAsset(editingId, payload)
        : await createFileAsset(payload);
      setFiles(updated);
      setForm(defaultForm());
      setEditingId(null);
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Ошибка при сохранении файла");
    }
  };

  const startEdit = (file: FileAsset) => {
    setEditingId(file.id);
    setForm({
      product_type: file.product_type,
      label: file.label,
      path: file.path,
      os_type: file.os_type || "",
      checksum: file.checksum || ""
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setForm(defaultForm());
  };

  const removeFile = async (id: number) => {
    if (!confirm("Удалить файл?")) return;
    try {
      const updated = await deleteFileAsset(id);
      setFiles(updated);
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Ошибка при удалении файла");
    }
  };

  return (
    <div className="card">
      <h2>Файлы VPN</h2>
      {error && <div className="alert">{error}</div>}
      <form className="inline-form" onSubmit={handleSubmit}>
        <input
          placeholder="Тип товара"
          value={form.product_type}
          onChange={(e) => setForm((prev) => ({ ...prev, product_type: e.target.value }))}
          required
        />
        <input
          placeholder="Название"
          value={form.label}
          onChange={(e) => setForm((prev) => ({ ...prev, label: e.target.value }))}
          required
        />
        <input
          placeholder="Путь (например windows/config.ovpn)"
          value={form.path}
          onChange={(e) => setForm((prev) => ({ ...prev, path: e.target.value }))}
          required
        />
        <input
          placeholder="OS"
          value={form.os_type}
          onChange={(e) => setForm((prev) => ({ ...prev, os_type: e.target.value }))}
        />
        <input
          placeholder="Checksum"
          value={form.checksum}
          onChange={(e) => setForm((prev) => ({ ...prev, checksum: e.target.value }))}
        />
        <div className="actions">
          <button type="submit" className="primary">
            {editingId ? "Сохранить" : "Добавить"}
          </button>
          {editingId && (
            <button type="button" className="secondary" onClick={cancelEdit}>
              Отмена
            </button>
          )}
        </div>
      </form>

      {loading ? (
        <p>Загрузка...</p>
      ) : (
        <table className="table" style={{ marginTop: "1.5rem" }}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Тип</th>
              <th>Название</th>
              <th>Путь</th>
              <th>OS</th>
              <th>Checksum</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {files.map((file) => (
              <tr key={file.id}>
                <td>{file.id}</td>
                <td>{file.product_type}</td>
                <td>{file.label}</td>
                <td>{file.path}</td>
                <td>{file.os_type || "—"}</td>
                <td>{file.checksum || "—"}</td>
                <td>
                  <div className="actions">
                    <button className="secondary" onClick={() => startEdit(file)}>
                      Изменить
                    </button>
                    <button className="secondary" onClick={() => removeFile(file.id)}>
                      Удалить
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default FilesPage;
