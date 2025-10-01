export type SalesRecord = {
  date: string;
  Sales: number;
  Profit: number;
  Expenses: number;
  Customers: number;
};

export type ProductPerformanceRecord = {
  name: string;
  sales: number;
  growth: number;
  units: number;
};

export type CategoryRecord = {
  name: string;
  value: number;
  growth: number;
};

export type RegionalRecord = {
  region: string;
  sales: number;
  marketShare: number;
};

export type DemographicRecord = {
  ageGroup: string;
  percentage: number;
  spending: number;
};

export type DashboardMetrics = {
  totalRevenue: number;
  totalProfit: number;
  totalCustomers: number;
  conversionRate: string;
  averageOrderValue: string;
  profitMargin: string;
};

export interface DashboardDataPayload {
  salesData: SalesRecord[];
  productData: ProductPerformanceRecord[];
  categoryData: CategoryRecord[];
  regionalData: RegionalRecord[];
  demographicsData: DemographicRecord[];
  metrics: DashboardMetrics;
}

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null;

const isFiniteNumber = (value: unknown): value is number =>
  typeof value === "number" && Number.isFinite(value);

const isString = (value: unknown): value is string => typeof value === "string";

const isSalesRecord = (value: unknown): value is SalesRecord => {
  if (!isRecord(value)) {
    return false;
  }
  const record = value as Record<string, unknown>;
  return (
    isString(record.date) &&
    isFiniteNumber(record.Sales) &&
    isFiniteNumber(record.Profit) &&
    isFiniteNumber(record.Expenses) &&
    isFiniteNumber(record.Customers)
  );
};

const isProductPerformanceRecord = (value: unknown): value is ProductPerformanceRecord => {
  if (!isRecord(value)) {
    return false;
  }
  const record = value as Record<string, unknown>;
  return (
    isString(record.name) &&
    isFiniteNumber(record.sales) &&
    isFiniteNumber(record.growth) &&
    isFiniteNumber(record.units)
  );
};

const isCategoryRecord = (value: unknown): value is CategoryRecord => {
  if (!isRecord(value)) {
    return false;
  }
  const record = value as Record<string, unknown>;
  return (
    isString(record.name) &&
    isFiniteNumber(record.value) &&
    isFiniteNumber(record.growth)
  );
};

const isRegionalRecord = (value: unknown): value is RegionalRecord => {
  if (!isRecord(value)) {
    return false;
  }
  const record = value as Record<string, unknown>;
  return (
    isString(record.region) &&
    isFiniteNumber(record.sales) &&
    isFiniteNumber(record.marketShare)
  );
};

const isDemographicRecord = (value: unknown): value is DemographicRecord => {
  if (!isRecord(value)) {
    return false;
  }
  const record = value as Record<string, unknown>;
  return (
    isString(record.ageGroup) &&
    isFiniteNumber(record.percentage) &&
    isFiniteNumber(record.spending)
  );
};

const isDashboardMetrics = (value: unknown): value is DashboardMetrics => {
  if (!isRecord(value)) {
    return false;
  }
  const metrics = value as Record<string, unknown>;
  return (
    isFiniteNumber(metrics.totalRevenue) &&
    isFiniteNumber(metrics.totalProfit) &&
    isFiniteNumber(metrics.totalCustomers) &&
    isString(metrics.conversionRate) &&
    isString(metrics.averageOrderValue) &&
    isString(metrics.profitMargin)
  );
};

export const isDashboardDataPayload = (value: unknown): value is DashboardDataPayload => {
  if (!isRecord(value)) {
    return false;
  }

  const data = value as Record<string, unknown>;
  const sales = data.salesData;
  const products = data.productData;
  const categories = data.categoryData;
  const regions = data.regionalData;
  const demographics = data.demographicsData;
  const metrics = data.metrics;

  return (
    Array.isArray(sales) && sales.every(isSalesRecord) &&
    Array.isArray(products) && products.every(isProductPerformanceRecord) &&
    Array.isArray(categories) && categories.every(isCategoryRecord) &&
    Array.isArray(regions) && regions.every(isRegionalRecord) &&
    Array.isArray(demographics) && demographics.every(isDemographicRecord) &&
    isDashboardMetrics(metrics)
  );
};
