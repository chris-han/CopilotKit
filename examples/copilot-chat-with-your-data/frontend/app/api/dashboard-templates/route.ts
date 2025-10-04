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
    const params: any[] = [];
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
    return NextResponse.json(
      { error: "Failed to fetch dashboard templates" },
      { status: 500 }
    );
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