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

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  try {

    // Check if database configuration is available
    if (!process.env.POSTGRES_HOST || !process.env.POSTGRES_USER) {
      console.warn("Database not configured, returning mock dashboard");
      const mockDashboard = {
        id,
        name: "Mock Dashboard",
        description: "This is a mock dashboard (database unavailable)",
        layout_config: {
          grid: { cols: 4, rows: "auto" },
          items: []
        },
        metadata: {},
        is_public: false,
        created_by: "anonymous",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      return NextResponse.json(mockDashboard);
    }

    const query = `
      SELECT id, name, description, layout_config, metadata, is_public, created_by, created_at, updated_at
      FROM dashboards.dashboards
      WHERE id = $1
    `;

    const result = await pool.query(query, [id]);

    if (result.rows.length === 0) {
      return NextResponse.json(
        { error: "Dashboard not found" },
        { status: 404 }
      );
    }

    return NextResponse.json(result.rows[0]);
  } catch (error) {
    console.error("Database error:", error);
    console.warn("Database unavailable, returning mock dashboard");
    const mockDashboard = {
      id,
      name: "Mock Dashboard",
      description: "This is a mock dashboard (database unavailable)",
      layout_config: {
        grid: { cols: 4, rows: "auto" },
        items: []
      },
      metadata: {},
      is_public: false,
      created_by: "anonymous",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    return NextResponse.json(mockDashboard);
  }
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const body = await request.json();
  const { name, description, layout_config, metadata, is_public } = body;

  try {

    // Check if database configuration is available
    if (!process.env.POSTGRES_HOST || !process.env.POSTGRES_USER) {
      console.warn("Database not configured, returning mock updated dashboard");
      const mockDashboard = {
        id,
        name: name || "Mock Dashboard",
        description: description || "This is a mock dashboard (database unavailable)",
        layout_config: layout_config || { grid: { cols: 4, rows: "auto" }, items: [] },
        metadata: metadata || {},
        is_public: is_public || false,
        created_by: "anonymous",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      return NextResponse.json(mockDashboard);
    }

    // Build dynamic update query
    const updates: string[] = [];
    const values: Array<string | number | boolean> = [];
    let paramIndex = 1;

    if (name !== undefined) {
      updates.push(`name = $${paramIndex++}`);
      values.push(name);
    }
    if (description !== undefined) {
      updates.push(`description = $${paramIndex++}`);
      values.push(description);
    }
    if (layout_config !== undefined) {
      updates.push(`layout_config = $${paramIndex++}`);
      values.push(JSON.stringify(layout_config));
    }
    if (metadata !== undefined) {
      updates.push(`metadata = $${paramIndex++}`);
      values.push(JSON.stringify(metadata));
    }
    if (is_public !== undefined) {
      updates.push(`is_public = $${paramIndex++}`);
      values.push(is_public);
    }

    if (updates.length === 0) {
      return NextResponse.json(
        { error: "No updates provided" },
        { status: 400 }
      );
    }

    updates.push(`updated_at = NOW()`);
    values.push(id);

    const query = `
      UPDATE dashboards.dashboards
      SET ${updates.join(", ")}
      WHERE id = $${paramIndex}
      RETURNING id, name, description, layout_config, metadata, is_public, created_by, created_at, updated_at
    `;

    const result = await pool.query(query, values);

    if (result.rows.length === 0) {
      return NextResponse.json(
        { error: "Dashboard not found" },
        { status: 404 }
      );
    }

    return NextResponse.json(result.rows[0]);
  } catch (error) {
    console.error("Database error:", error);
    console.warn("Database unavailable, returning mock updated dashboard");
    const mockDashboard = {
      id,
      name: name || "Mock Dashboard",
      description: description || "This is a mock dashboard (database unavailable)",
      layout_config: layout_config || { grid: { cols: 4, rows: "auto" }, items: [] },
      metadata: metadata || {},
      is_public: is_public || false,
      created_by: "anonymous",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    return NextResponse.json(mockDashboard);
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  try {
    const query = `
      DELETE FROM dashboards.dashboards
      WHERE id = $1
      RETURNING id
    `;

    const result = await pool.query(query, [id]);

    if (result.rows.length === 0) {
      return NextResponse.json(
        { error: "Dashboard not found" },
        { status: 404 }
      );
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Database error:", error);
    return NextResponse.json(
      { error: "Failed to delete dashboard" },
      { status: 500 }
    );
  }
}
