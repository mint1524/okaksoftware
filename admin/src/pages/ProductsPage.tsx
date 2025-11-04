import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  createProduct,
  createVariant,
  deleteProduct,
  deleteVariant,
  fetchProducts,
  updateProduct,
  updateVariant
} from "../api/client";
import type { Product, ProductVariant } from "../types";

interface ProductFormState {
  title: string;
  slug: string;
  type: string;
  description: string;
  support_contact: string;
  domain_hint: string;
  metadata: string;
  is_active: boolean;
}

const defaultProductForm = (): ProductFormState => ({
  title: "",
  slug: "",
  type: "",
  description: "",
  support_contact: "",
  domain_hint: "",
  metadata: "",
  is_active: true
});

interface VariantFormState {
  name: string;
  price: string;
  currency: string;
  digiseller_product_id: string;
  payment_url: string;
  sort_order: string;
  metadata: string;
}

const defaultVariantForm = (): VariantFormState => ({
  name: "",
  price: "0",
  currency: "RUB",
  digiseller_product_id: "",
  payment_url: "",
  sort_order: "0",
  metadata: ""
});

const ProductsPage = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [productForm, setProductForm] = useState<ProductFormState>(defaultProductForm);
  const [editingProductId, setEditingProductId] = useState<number | null>(null);
  const [variantForms, setVariantForms] = useState<Record<number, VariantFormState>>({});
  const [editingVariantId, setEditingVariantId] = useState<number | null>(null);
  const [variantEditForm, setVariantEditForm] = useState<VariantFormState>(defaultVariantForm);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchProducts();
        setProducts(data);
        setError(null);
      } catch (err) {
        console.error(err);
        setError("Не удалось загрузить товары");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const resetVariantFormFor = (productId: number) => {
    setVariantForms((prev) => ({ ...prev, [productId]: defaultVariantForm() }));
  };

  const parseMetadata = (value: string): Record<string, unknown> | undefined => {
    if (!value) return undefined;
    try {
      return JSON.parse(value);
    } catch (err) {
      console.error(err);
      setError("Некорректный JSON в поле metadata");
      return undefined;
    }
  };

  const handleCreateProduct = async (event: FormEvent) => {
    event.preventDefault();
    const metadata = parseMetadata(productForm.metadata);
    if (productForm.metadata && metadata === undefined) {
      return;
    }
    try {
      const payload: Record<string, unknown> = {
        title: productForm.title,
        slug: productForm.slug,
        type: productForm.type,
        description: productForm.description || null,
        support_contact: productForm.support_contact || null,
        domain_hint: productForm.domain_hint || null,
        is_active: productForm.is_active
      };
      if (metadata !== undefined) {
        payload.metadata = metadata;
      }
      const updated = await createProduct(payload);
      setProducts(updated);
      setProductForm(defaultProductForm());
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Ошибка при создании товара");
    }
  };

  const startEditProduct = (product: Product) => {
    setEditingProductId(product.id);
    setProductForm({
      title: product.title,
      slug: product.slug,
      type: product.type,
      description: product.description || "",
      support_contact: product.support_contact || "",
      domain_hint: product.domain_hint || "",
      metadata: product.metadata ? JSON.stringify(product.metadata, null, 2) : "",
      is_active: product.is_active
    });
  };

  const submitEditProduct = async (event: FormEvent) => {
    event.preventDefault();
    if (!editingProductId) return;
    const metadata = parseMetadata(productForm.metadata);
    if (productForm.metadata && metadata === undefined) {
      return;
    }
    try {
      const payload: Record<string, unknown> = {};
      payload.title = productForm.title;
      payload.slug = productForm.slug;
      payload.type = productForm.type;
      payload.description = productForm.description || null;
      payload.support_contact = productForm.support_contact || null;
      payload.domain_hint = productForm.domain_hint || null;
      payload.is_active = productForm.is_active;
      if (metadata !== undefined) {
        payload.metadata = metadata;
      }
      const updated = await updateProduct(editingProductId, payload);
      setProducts(updated);
      setEditingProductId(null);
      setProductForm(defaultProductForm());
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Ошибка при обновлении товара");
    }
  };

  const cancelEdit = () => {
    setEditingProductId(null);
    setProductForm(defaultProductForm());
  };

  const toggleActive = async (product: Product) => {
    try {
      const updated = await updateProduct(product.id, { is_active: !product.is_active });
      setProducts(updated);
    } catch (err) {
      console.error(err);
      setError("Не удалось изменить статус товара");
    }
  };

  const removeProduct = async (productId: number) => {
    if (!confirm("Удалить товар?")) return;
    try {
      const updated = await deleteProduct(productId);
      setProducts(updated);
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Ошибка при удалении товара");
    }
  };

  const handleCreateVariant = async (event: FormEvent, product: Product) => {
    event.preventDefault();
    const form = variantForms[product.id] || defaultVariantForm();
    const metadata = parseMetadata(form.metadata);
    if (form.metadata && metadata === undefined) {
      return;
    }
    const price = parseFloat(form.price);
    const sort_order = parseInt(form.sort_order || "0", 10);
    if (Number.isNaN(price)) {
      setError("Цена указана неверно");
      return;
    }
    try {
      const payload: Record<string, unknown> = {
        name: form.name,
        price,
        currency: form.currency,
        digiseller_product_id: form.digiseller_product_id || null,
        payment_url: form.payment_url || null,
        sort_order
      };
      if (metadata !== undefined) {
        payload.metadata = metadata;
      }
      const updated = await createVariant(product.id, payload);
      setProducts(updated);
      resetVariantFormFor(product.id);
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Ошибка при добавлении тарифа");
    }
  };

  const startEditVariant = (variant: ProductVariant) => {
    setEditingVariantId(variant.id);
    setVariantEditForm({
      name: variant.name,
      price: variant.price.toString(),
      currency: variant.currency,
      digiseller_product_id: variant.digiseller_product_id || "",
      payment_url: variant.payment_url || "",
      sort_order: variant.sort_order.toString(),
      metadata: variant.metadata ? JSON.stringify(variant.metadata, null, 2) : ""
    });
  };

  const submitEditVariant = async (event: FormEvent) => {
    event.preventDefault();
    if (!editingVariantId) return;
    const metadata = parseMetadata(variantEditForm.metadata);
    if (variantEditForm.metadata && metadata === undefined) {
      return;
    }
    const price = parseFloat(variantEditForm.price);
    const sort_order = parseInt(variantEditForm.sort_order || "0", 10);
    if (Number.isNaN(price)) {
      setError("Цена указана неверно");
      return;
    }
    try {
      const payload: Record<string, unknown> = {
        name: variantEditForm.name,
        price,
        currency: variantEditForm.currency,
        digiseller_product_id: variantEditForm.digiseller_product_id || null,
        payment_url: variantEditForm.payment_url || null,
        sort_order
      };
      if (metadata !== undefined) {
        payload.metadata = metadata;
      }
      const updated = await updateVariant(editingVariantId, payload);
      setProducts(updated);
      setEditingVariantId(null);
      setVariantEditForm(defaultVariantForm());
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Ошибка при обновлении тарифа");
    }
  };

  const cancelVariantEdit = () => {
    setEditingVariantId(null);
    setVariantEditForm(defaultVariantForm());
  };

  const removeVariant = async (variantId: number) => {
    if (!confirm("Удалить тариф?")) return;
    try {
      const updated = await deleteVariant(variantId);
      setProducts(updated);
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Ошибка при удалении тарифа");
    }
  };

  const handleVariantFormChange = (productId: number, key: keyof VariantFormState, value: string) => {
    setVariantForms((prev) => ({
      ...prev,
      [productId]: {
        ...(prev[productId] || defaultVariantForm()),
        [key]: value
      }
    }));
  };

  const sortedProducts = useMemo(() => {
    return [...products].sort((a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
  }, [products]);

  return (
    <div className="card">
      <h2>Товары</h2>
      {error && <div className="alert">{error}</div>}
      <form className="inline-form" onSubmit={editingProductId ? submitEditProduct : handleCreateProduct}>
        <input
          placeholder="Название"
          value={productForm.title}
          onChange={(e) => setProductForm((prev) => ({ ...prev, title: e.target.value }))}
          required
        />
        <input
          placeholder="Slug"
          value={productForm.slug}
          onChange={(e) => setProductForm((prev) => ({ ...prev, slug: e.target.value }))}
          required
        />
        <input
          placeholder="Тип (gpt/vpn)"
          value={productForm.type}
          onChange={(e) => setProductForm((prev) => ({ ...prev, type: e.target.value }))}
          required
        />
        <input
          placeholder="Контакты поддержки"
          value={productForm.support_contact}
          onChange={(e) => setProductForm((prev) => ({ ...prev, support_contact: e.target.value }))}
        />
        <input
          placeholder="Поддомен"
          value={productForm.domain_hint}
          onChange={(e) => setProductForm((prev) => ({ ...prev, domain_hint: e.target.value }))}
        />
        <textarea
          placeholder="Описание"
          value={productForm.description}
          onChange={(e) => setProductForm((prev) => ({ ...prev, description: e.target.value }))}
          rows={2}
        />
        <textarea
          placeholder='Metadata (JSON)'
          value={productForm.metadata}
          onChange={(e) => setProductForm((prev) => ({ ...prev, metadata: e.target.value }))}
          rows={2}
        />
        <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <input
            type="checkbox"
            checked={productForm.is_active}
            onChange={(e) => setProductForm((prev) => ({ ...prev, is_active: e.target.checked }))}
          />
          Активен
        </label>
        <div className="actions">
          <button type="submit" className="primary">
            {editingProductId ? "Сохранить" : "Добавить"}
          </button>
          {editingProductId && (
            <button type="button" className="secondary" onClick={cancelEdit}>
              Отмена
            </button>
          )}
        </div>
      </form>

      {loading ? (
        <p>Загрузка...</p>
      ) : (
        <div className="grid" style={{ marginTop: "1.5rem", gap: "1rem" }}>
          {sortedProducts.map((product) => (
            <div className="product-card" key={product.id}>
              <div>
                <div className="badge">{product.type}</div>
                <h3>{product.title}</h3>
                <p>{product.description || "Без описания"}</p>
                <p>Slug: {product.slug}</p>
                <p>Поддержка: {product.support_contact || "—"}</p>
                <p>Поддомен: {product.domain_hint || "—"}</p>
                <p>Статус: {product.is_active ? "Активен" : "Выключен"}</p>
              </div>
              <div className="actions">
                <button className="secondary" onClick={() => toggleActive(product)}>
                  {product.is_active ? "Выключить" : "Включить"}
                </button>
                <button className="secondary" onClick={() => startEditProduct(product)}>
                  Изменить
                </button>
                <button className="secondary" onClick={() => removeProduct(product.id)}>
                  Удалить
                </button>
              </div>

              <div className="variant-list">
                <strong>Тарифы</strong>
                {product.variants.map((variant) => (
                  <div key={variant.id}>
                    <div className="variant-item">
                      <div>
                        <div>{variant.name}</div>
                        <small>
                          {variant.price} {variant.currency} · сортировка {variant.sort_order}
                        </small>
                      </div>
                      <div className="actions">
                        <button className="secondary" onClick={() => startEditVariant(variant)}>
                          Изменить
                        </button>
                        <button className="secondary" onClick={() => removeVariant(variant.id)}>
                          Удалить
                        </button>
                      </div>
                    </div>
                    {editingVariantId === variant.id && (
                      <form className="inline-form" onSubmit={submitEditVariant}>
                        <input
                          placeholder="Название"
                          value={variantEditForm.name}
                          onChange={(e) => setVariantEditForm((prev) => ({ ...prev, name: e.target.value }))}
                          required
                        />
                        <input
                          placeholder="Цена"
                          value={variantEditForm.price}
                          onChange={(e) => setVariantEditForm((prev) => ({ ...prev, price: e.target.value }))}
                          required
                        />
                        <input
                          placeholder="Валюта"
                          value={variantEditForm.currency}
                          onChange={(e) => setVariantEditForm((prev) => ({ ...prev, currency: e.target.value }))}
                          required
                        />
                        <input
                          placeholder="Внешний ID"
                          value={variantEditForm.digiseller_product_id}
                          onChange={(e) =>
                            setVariantEditForm((prev) => ({ ...prev, digiseller_product_id: e.target.value }))
                          }
                        />
                        <input
                          placeholder="Payment URL"
                          value={variantEditForm.payment_url}
                          onChange={(e) => setVariantEditForm((prev) => ({ ...prev, payment_url: e.target.value }))}
                        />
                        <input
                          placeholder="Сортировка"
                          value={variantEditForm.sort_order}
                          onChange={(e) => setVariantEditForm((prev) => ({ ...prev, sort_order: e.target.value }))}
                        />
                        <textarea
                          placeholder="Metadata JSON"
                          value={variantEditForm.metadata}
                          onChange={(e) => setVariantEditForm((prev) => ({ ...prev, metadata: e.target.value }))}
                          rows={2}
                        />
                        <div className="actions">
                          <button type="submit" className="primary">
                            Сохранить тариф
                          </button>
                          <button type="button" className="secondary" onClick={cancelVariantEdit}>
                            Отмена
                          </button>
                        </div>
                      </form>
                    )}
                  </div>
                ))}

                <form className="inline-form" onSubmit={(event) => handleCreateVariant(event, product)}>
                  <input
                    placeholder="Название"
                    value={(variantForms[product.id] || defaultVariantForm()).name}
                    onChange={(e) => handleVariantFormChange(product.id, "name", e.target.value)}
                    required
                  />
                  <input
                    placeholder="Цена"
                    value={(variantForms[product.id] || defaultVariantForm()).price}
                    onChange={(e) => handleVariantFormChange(product.id, "price", e.target.value)}
                    required
                  />
                  <input
                    placeholder="Валюта"
                    value={(variantForms[product.id] || defaultVariantForm()).currency}
                    onChange={(e) => handleVariantFormChange(product.id, "currency", e.target.value)}
                    required
                  />
                  <input
                    placeholder="Внешний ID"
                    value={(variantForms[product.id] || defaultVariantForm()).digiseller_product_id}
                    onChange={(e) => handleVariantFormChange(product.id, "digiseller_product_id", e.target.value)}
                  />
                  <input
                    placeholder="Payment URL"
                    value={(variantForms[product.id] || defaultVariantForm()).payment_url}
                    onChange={(e) => handleVariantFormChange(product.id, "payment_url", e.target.value)}
                  />
                  <input
                    placeholder="Сортировка"
                    value={(variantForms[product.id] || defaultVariantForm()).sort_order}
                    onChange={(e) => handleVariantFormChange(product.id, "sort_order", e.target.value)}
                  />
                  <textarea
                    placeholder="Metadata JSON"
                    value={(variantForms[product.id] || defaultVariantForm()).metadata}
                    onChange={(e) => handleVariantFormChange(product.id, "metadata", e.target.value)}
                    rows={2}
                  />
                  <button type="submit" className="primary">
                    Добавить тариф
                  </button>
                </form>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ProductsPage;
