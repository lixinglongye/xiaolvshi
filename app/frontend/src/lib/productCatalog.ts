import { client } from '@/lib/api';

export interface ProductCatalogItem {
  sku: string;
  plan_type: string | null;
  name: string;
  description: string;
  amount: number;
  currency: string;
  display_price: string;
  interval: string | null;
  highlight: boolean;
  features: string[];
  report_quota_monthly?: number | null;
  team_seats?: number | null;
}

export async function getProductCatalog(locale: string): Promise<ProductCatalogItem[]> {
  const response = await client.apiCall.invoke({
    url: `/api/v1/payment/catalog?locale=${encodeURIComponent(locale)}`,
    method: 'GET',
  });
  return response?.data?.items ?? [];
}

export async function getProductBySku(locale: string, sku: string): Promise<ProductCatalogItem | null> {
  const items = await getProductCatalog(locale);
  return items.find((item) => item.sku === sku) ?? null;
}
