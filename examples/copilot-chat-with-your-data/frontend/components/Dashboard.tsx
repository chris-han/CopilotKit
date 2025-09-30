"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { AreaChart } from "./ui/area-chart";
import { BarChart } from "./ui/bar-chart";
import { DonutChart } from "./ui/pie-chart";
import { 
  salesData, 
  productData, 
  categoryData, 
  regionalData,
  demographicsData,
  calculateTotalRevenue,
  calculateTotalProfit,
  calculateTotalCustomers,
  calculateConversionRate,
  calculateAverageOrderValue,
  calculateProfitMargin
} from "../data/dashboard-data";

export function Dashboard() {
  // Calculate metrics
  const totalRevenue = calculateTotalRevenue();
  const totalProfit = calculateTotalProfit();
  const totalCustomers = calculateTotalCustomers();
  const conversionRate = calculateConversionRate();
  const averageOrderValue = calculateAverageOrderValue();
  const profitMargin = calculateProfitMargin();

  const keyMetrics = [
    { label: "Total Revenue", value: `$${totalRevenue.toLocaleString()}` },
    { label: "Total Profit", value: `$${totalProfit.toLocaleString()}` },
    { label: "Customers", value: totalCustomers.toLocaleString() },
    { label: "Conversion Rate", value: conversionRate },
    { label: "Avg Order Value", value: `$${averageOrderValue}` },
    { label: "Profit Margin", value: profitMargin }
  ];

  // Color palettes for different charts
  const colors = {
    salesOverview: ["#3b82f6", "#10b981", "#ef4444"],  // Blue, Green, Red
    productPerformance: ["#8b5cf6", "#6366f1", "#4f46e5"],  // Purple spectrum
    categories: ["#3b82f6", "#64748b", "#10b981", "#f59e0b", "#94a3b8"],  // Mixed
    regional: ["#059669", "#10b981", "#34d399", "#6ee7b7", "#a7f3d0"],  // Green spectrum
    demographics: ["#f97316", "#f59e0b", "#eab308", "#facc15", "#fde047"]  // Orange to Yellow
  };
  
  return (
    <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-4 w-full">
      {/* Key Metrics */}
      <div className="col-span-1 md:col-span-2 lg:col-span-4">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {keyMetrics.map((metric) => (
            <Card key={metric.label} className="gap-2 py-4">
              <CardHeader className="px-4 py-0">
                <CardDescription className="text-xs text-muted-foreground">
                  {metric.label}
                </CardDescription>
              </CardHeader>
              <CardContent className="px-4 py-0">
                <CardTitle className="text-xl text-card-foreground">
                  {metric.value}
                </CardTitle>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Charts */}
      <Card className="col-span-1 md:col-span-2 lg:col-span-4" data-chart-id="sales-overview">
        <CardHeader className="pb-1 pt-3">
          <CardTitle className="text-base font-medium">Sales Overview</CardTitle>
          <CardDescription className="text-xs">Monthly sales and profit data</CardDescription>
        </CardHeader>
        <CardContent className="p-3">
          <div className="h-60">
            <AreaChart
              data={salesData}
              index="date"
              categories={["Sales", "Profit", "Expenses"]}
              colors={colors.salesOverview}
              valueFormatter={(value) => `$${value.toLocaleString()}`}
              showLegend={true}
              showGrid={true}
              showXAxis={true}
              showYAxis={true}
            />
          </div>
        </CardContent>
      </Card>

      <Card className="col-span-1 md:col-span-1 lg:col-span-2" data-chart-id="product-performance">
        <CardHeader className="pb-1 pt-3">
          <CardTitle className="text-base font-medium">Product Performance</CardTitle>
          <CardDescription className="text-xs">Top selling products</CardDescription>
        </CardHeader>
        <CardContent className="p-3">
          <div className="h-60">
            <BarChart
              data={productData}
              index="name"
              categories={["sales"]}
              colors={colors.productPerformance}
              valueFormatter={(value) => `$${value.toLocaleString()}`}
              showLegend={false}
              showGrid={true}
              layout="horizontal"
            />
          </div>
        </CardContent>
      </Card>

      <Card className="col-span-1 md:col-span-1 lg:col-span-2" data-chart-id="sales-by-category">
        <CardHeader className="pb-1 pt-3">
          <CardTitle className="text-base font-medium">Sales by Category</CardTitle>
          <CardDescription className="text-xs">Distribution across categories</CardDescription>
        </CardHeader>
        <CardContent className="p-3">
          <div className="h-60">
            <DonutChart
              data={categoryData}
              category="value"
              index="name"
              valueFormatter={(value) => `${value}%`}
              colors={colors.categories}
              centerText="Categories"
              paddingAngle={0}
              showLabel={false}
              showLegend={true}
              innerRadius={45}
              outerRadius="90%"
            />
          </div>
        </CardContent>
      </Card>

      <Card className="col-span-1 md:col-span-1 lg:col-span-2" data-chart-id="regional-sales">
        <CardHeader className="pb-1 pt-3">
          <CardTitle className="text-base font-medium">Regional Sales</CardTitle>
          <CardDescription className="text-xs">Sales by geographic region</CardDescription>
        </CardHeader>
        <CardContent className="p-3">
          <div className="h-60">
            <BarChart
              data={regionalData}
              index="region"
              categories={["sales"]}
              colors={colors.regional}
              valueFormatter={(value) => `$${value.toLocaleString()}`}
              showLegend={false}
              showGrid={true}
              layout="horizontal"
            />
          </div>
        </CardContent>
      </Card>

      <Card className="col-span-1 md:col-span-1 lg:col-span-2" data-chart-id="customer-demographics">
        <CardHeader className="pb-1 pt-3">
          <CardTitle className="text-base font-medium">Customer Demographics</CardTitle>
          <CardDescription className="text-xs">Spending by age group</CardDescription>
        </CardHeader>
        <CardContent className="p-3">
          <div className="h-60">
            <BarChart
              data={demographicsData}
              index="ageGroup"
              categories={["spending"]}
              colors={colors.demographics}
              valueFormatter={(value) => `$${value}`}
              showLegend={false}
              showGrid={true}
              layout="horizontal"
            />
          </div>
        </CardContent>
      </Card>


      <Card className="col-span-1 md:col-span-2 lg:col-span-4" data-chart-id="strategic-commentary">
        <CardHeader className="pb-1 pt-3">
          <CardTitle className="text-base font-medium">Strategic Commentary</CardTitle>
          <CardDescription className="text-xs">Risks, opportunities, and recommendations</CardDescription>
        </CardHeader>
        <CardContent className="p-3">
          <div className="h-full">
            
            {/* text entry area */}
            <textarea
              className="w-full h-32 p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Type your insights and recommendations here..."
            ></textarea>
            
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 
