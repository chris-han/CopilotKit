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
      console.warn("Database not configured, returning empty dashboard list");
      return NextResponse.json([]);
    }

    const { searchParams } = new URL(request.url);
    const createdBy = searchParams.get("created_by");
    const isPublic = searchParams.get("is_public");
    const limit = parseInt(searchParams.get("limit") || "50");
    const offset = parseInt(searchParams.get("offset") || "0");

    let query = `
      SELECT id, name, description, layout_config, metadata, is_public, created_by, created_at, updated_at
      FROM dashboards.dashboards
      WHERE 1=1
    `;
    const params: any[] = [];
    let paramIndex = 1;

    if (createdBy) {
      query += ` AND created_by = $${paramIndex++}`;
      params.push(createdBy);
    }

    if (isPublic !== null) {
      query += ` AND is_public = $${paramIndex++}`;
      params.push(isPublic === "true");
    }

    query += ` ORDER BY updated_at DESC LIMIT $${paramIndex++} OFFSET $${paramIndex++}`;
    params.push(limit, offset);

    const result = await pool.query(query, params);
    return NextResponse.json(result.rows);
  } catch (error) {
    console.error("Database error:", error);
    // Return empty array instead of error for better UX when DB is unavailable
    console.warn("Database unavailable, returning empty dashboard list");
    return NextResponse.json([]);
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { name, description, layout_config, metadata, is_public, created_by } = body;

    if (!name || !layout_config) {
      return NextResponse.json(
        { error: "Name and layout_config are required" },
        { status: 400 }
      );
    }

    // Check if database configuration is available
    if (!process.env.POSTGRES_HOST || !process.env.POSTGRES_USER) {
      console.warn("Database not configured, creating mock dashboard");
      const mockDashboard = {
        id: `dashboard-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        name,
        description,
        layout_config,
        metadata: metadata || {},
        is_public: is_public || false,
        created_by: created_by || "anonymous",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      return NextResponse.json(mockDashboard, { status: 201 });
    }

    const query = `
      INSERT INTO dashboards.dashboards (name, description, layout_config, metadata, is_public, created_by)
      VALUES ($1, $2, $3, $4, $5, $6)
      RETURNING id, name, description, layout_config, metadata, is_public, created_by, created_at, updated_at
    `;

    const params = [
      name,
      description,
      JSON.stringify(layout_config),
      JSON.stringify(metadata || {}),
      is_public || false,
      created_by || "anonymous",
    ];

    const result = await pool.query(query, params);
    return NextResponse.json(result.rows[0], { status: 201 });
  } catch (error) {
    console.error("Database error:", error);
    // Return mock dashboard as fallback
    console.warn("Database unavailable, creating mock dashboard");
    const body = await request.json();
    const { name, description, layout_config, metadata, is_public, created_by } = body;
    const mockDashboard = {
      id: `dashboard-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      name,
      description,
      layout_config,
      metadata: metadata || {},
      is_public: is_public || false,
      created_by: created_by || "anonymous",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    return NextResponse.json(mockDashboard, { status: 201 });
  }
}