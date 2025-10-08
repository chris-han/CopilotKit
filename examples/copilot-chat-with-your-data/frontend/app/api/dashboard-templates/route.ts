import { NextRequest, NextResponse } from "next/server";
import { Pool } from "pg";

// Initialize PostgreSQL connection
const pool = new Pool({
  host: process.env.POSTGRES_HOST,
  port: parseInt(process.env.POSTGRES_PORT || "5432"),
  database: process.env.POSTGRES_DB,
  user: process.env.POSTGRES_USER,
  password: process.env.POSTGRES_PASSWORD,
  ssl: process.env.POSTGRES_HOST?.includes("azure") ? { rejectUnauthorized: false } : false,
});

export async function GET(request: NextRequest) {
  try {
    // Check if database configuration is available
    if (!process.env.POSTGRES_HOST || !process.env.POSTGRES_USER) {
      console.warn("Database not configured, returning mock templates");
      const mockTemplates = [
        {
          id: "base-layout",
          name: "Base Layout",
          description: "Dynamic dashboard with live data, metrics, and AI-generated insights",
          category: "Analytics",
          thumbnail_url: null,
          layout_config: {
            grid: { cols: 4, rows: "auto" },
            items: [
              {
                id: "metrics-overview",
                type: "metric",
                title: "Key Metrics",
                description: "Live performance indicators",
                span: "col-span-1 md:col-span-2 lg:col-span-4",
                position: { row: 1 },
                config: { type: "metrics" }
              },
              {
                id: "sales-overview",
                type: "chart",
                chartType: "area",
                title: "Sales Overview",
                description: "Monthly performance across revenue, profit, and expense lines",
                span: "col-span-1 md:col-span-2 lg:col-span-4",
                position: { row: 2 },
                config: { data_source: "salesData" }
              },
              {
                id: "product-performance",
                type: "chart",
                chartType: "bar",
                title: "Product Performance",
                description: "Auto-generated view based on dashboard dataset",
                span: "col-span-1 md:col-span-1 lg:col-span-2",
                position: { row: 3 },
                config: { data_source: "productData" }
              },
              {
                id: "sales-by-category",
                type: "chart",
                chartType: "donut",
                title: "Sales by Category",
                description: "Proportional contribution by segment",
                span: "col-span-1 md:col-span-1 lg:col-span-2",
                position: { row: 3 },
                config: { data_source: "categoryData" }
              },
              {
                id: "regional-sales",
                type: "chart",
                chartType: "bar",
                title: "Regional Sales",
                description: "Auto-generated view based on dashboard dataset",
                span: "col-span-1 md:col-span-1 lg:col-span-2",
                position: { row: 4 },
                config: { data_source: "regionalData" }
              },
              {
                id: "customer-demographics",
                type: "chart",
                chartType: "donut",
                title: "Customer Demographics",
                description: "Proportional contribution by segment",
                span: "col-span-1 md:col-span-1 lg:col-span-2",
                position: { row: 4 },
                config: { data_source: "demographicsData" }
              },
              {
                id: "strategic-commentary",
                type: "commentary",
                title: "Strategic Commentary",
                description: "AI-authored risks, opportunities, and recommendations",
                span: "col-span-1 md:col-span-2 lg:col-span-4",
                position: { row: 5 },
                config: { type: "ai_commentary" }
              }
            ]
          },
          default_data: {},
          is_featured: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          id: "template-1",
          name: "Financial Overview",
          description: "Comprehensive financial dashboard with key metrics and trends",
          category: "Financial",
          thumbnail_url: null,
          layout_config: {
            grid: { cols: 4, rows: "auto" },
            items: []
          },
          default_data: {},
          is_featured: false,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          id: "template-2",
          name: "Cost Optimization",
          description: "Track and optimize your cloud costs with detailed analytics",
          category: "Financial",
          thumbnail_url: null,
          layout_config: {
            grid: { cols: 4, rows: "auto" },
            items: []
          },
          default_data: {},
          is_featured: false,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      ];
      return NextResponse.json(mockTemplates);
    }

    const { searchParams } = new URL(request.url);
    const category = searchParams.get("category");
    const isFeatured = searchParams.get("is_featured");
    const limit = parseInt(searchParams.get("limit") || "50");
    const offset = parseInt(searchParams.get("offset") || "0");

    let query = `
      SELECT id, name, description, thumbnail_url, category, layout_config, default_data, is_featured, created_at, updated_at
      FROM dashboards.dashboard_templates
      WHERE 1=1
    `;
    const params: Array<string | number | boolean> = [];
    let paramIndex = 1;

    if (category) {
      query += ` AND category = $${paramIndex++}`;
      params.push(category);
    }

    if (isFeatured !== null) {
      query += ` AND is_featured = $${paramIndex++}`;
      params.push(isFeatured === "true");
    }

    query += ` ORDER BY is_featured DESC, name ASC LIMIT $${paramIndex++} OFFSET $${paramIndex++}`;
    params.push(limit, offset);

    const result = await pool.query(query, params);
    return NextResponse.json(result.rows);
  } catch (error) {
    console.error("Database error:", error);
    console.warn("Database unavailable, returning mock templates");
    const mockTemplates = [
      {
        id: "base-layout",
        name: "Base Layout",
        description: "Dynamic dashboard with live data, metrics, and AI-generated insights",
        category: "Analytics",
        thumbnail_url: null,
        layout_config: {
          grid: { cols: 4, rows: "auto" },
          items: [
            {
              id: "metrics-overview",
              type: "metric",
              title: "Key Metrics",
              description: "Live performance indicators",
              span: "col-span-1 md:col-span-2 lg:col-span-4",
              position: { row: 1 },
              config: { type: "metrics" }
            },
            {
              id: "sales-overview",
              type: "chart",
              chartType: "area",
              title: "Sales Overview",
              description: "Monthly performance across revenue, profit, and expense lines",
              span: "col-span-1 md:col-span-2 lg:col-span-4",
              position: { row: 2 },
              config: { data_source: "salesData" }
            },
            {
              id: "product-performance",
              type: "chart",
              chartType: "bar",
              title: "Product Performance",
              description: "Auto-generated view based on dashboard dataset",
              span: "col-span-1 md:col-span-1 lg:col-span-2",
              position: { row: 3 },
              config: { data_source: "productData" }
            },
            {
              id: "sales-by-category",
              type: "chart",
              chartType: "donut",
              title: "Sales by Category",
              description: "Proportional contribution by segment",
              span: "col-span-1 md:col-span-1 lg:col-span-2",
              position: { row: 3 },
              config: { data_source: "categoryData" }
            },
            {
              id: "regional-sales",
              type: "chart",
              chartType: "bar",
              title: "Regional Sales",
              description: "Auto-generated view based on dashboard dataset",
              span: "col-span-1 md:col-span-1 lg:col-span-2",
              position: { row: 4 },
              config: { data_source: "regionalData" }
            },
            {
              id: "customer-demographics",
              type: "chart",
              chartType: "donut",
              title: "Customer Demographics",
              description: "Proportional contribution by segment",
              span: "col-span-1 md:col-span-1 lg:col-span-2",
              position: { row: 4 },
              config: { data_source: "demographicsData" }
            },
            {
              id: "strategic-commentary",
              type: "commentary",
              title: "Strategic Commentary",
              description: "AI-authored risks, opportunities, and recommendations",
              span: "col-span-1 md:col-span-2 lg:col-span-4",
              position: { row: 5 },
              config: { type: "ai_commentary" }
            }
          ]
        },
        default_data: {},
        is_featured: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        id: "template-1",
        name: "Financial Overview",
        description: "Comprehensive financial dashboard with key metrics and trends",
        category: "Financial",
        thumbnail_url: null,
        layout_config: {
          grid: { cols: 4, rows: "auto" },
          items: []
        },
        default_data: {},
        is_featured: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        id: "template-2",
        name: "Cost Optimization",
        description: "Track and optimize your cloud costs with detailed analytics",
        category: "Financial",
        thumbnail_url: null,
        layout_config: {
          grid: { cols: 4, rows: "auto" },
          items: []
        },
        default_data: {},
        is_featured: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    ];
    return NextResponse.json(mockTemplates);
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { name, description, thumbnail_url, category, layout_config, default_data, is_featured } = body;

    if (!name || !category || !layout_config) {
      return NextResponse.json(
        { error: "Name, category, and layout_config are required" },
        { status: 400 }
      );
    }

    const query = `
      INSERT INTO dashboards.dashboard_templates (name, description, thumbnail_url, category, layout_config, default_data, is_featured)
      VALUES ($1, $2, $3, $4, $5, $6, $7)
      RETURNING id, name, description, thumbnail_url, category, layout_config, default_data, is_featured, created_at, updated_at
    `;

    const params = [
      name,
      description,
      thumbnail_url,
      category,
      JSON.stringify(layout_config),
      JSON.stringify(default_data || {}),
      is_featured || false,
    ];

    const result = await pool.query(query, params);
    return NextResponse.json(result.rows[0], { status: 201 });
  } catch (error) {
    console.error("Database error:", error);
    return NextResponse.json(
      { error: "Failed to create dashboard template" },
      { status: 500 }
    );
  }
}
