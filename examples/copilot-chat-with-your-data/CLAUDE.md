# Claude Code Guidelines

## Core Principles

### 1. Integration Strategy - Preserve and Enhance

When implementing LIDA-enhanced analytics features, follow these integration principles:

1. **Preserve Existing Functionality**: All current AG-UI, data story, and chart components remain unchanged
2. **Extend with LIDA Intelligence**: Add `LidaEnhancedProvider` that works alongside existing `AgUiProvider`
3. **Add Migration Workflow**: New `/migration` route and components for Phase 3B ClickHouse integration
4. **Enhance Chart System**: Extend existing chart highlighting with LIDA-powered recommendations
5. **Maintain Import Patterns**: Use established `@/` alias for component imports and existing utility patterns

**Key Implementation Approach:**
- Zero disruption to existing workflows
- Gradual enhancement allowing progressive adoption
- Maintain compatibility with current AG-UI protocol
- Preserve sophisticated chart highlighting system
- Build upon existing ECharts integration rather than replacing it

This ensures teams can continue using existing functionality while gradually adopting LIDA-enhanced features without downtime or breaking changes.

## Development Guidelines

### Feature Development Process

**MANDATORY**: Before implementing any new feature, you MUST:

1. **Consult the Master Plan**: Review `frontend/design-specs/LIDA-ECharts-Implementation-Plan.md` to understand:
   - How your feature fits into the overall LIDA-enhanced architecture
   - Which implementation phase your feature belongs to
   - Dependencies and integration points with existing systems
   - Whether similar functionality is already planned or completed

2. **Design First, Code Second**: Create a clear design that follows the established patterns:
   - Identify if your feature requires UI navigation (direct context updates) or AI interactions (AgUI protocol)
   - Determine integration points with existing AG-UI, ECharts, and Data Assistant systems
   - Plan for LIDA intelligence enhancement where applicable
   - Consider persona-aware visualization selection if creating analytics features

3. **Preserve Integration Strategy**: Ensure your feature:
   - Maintains compatibility with existing AG-UI workflows
   - Extends rather than replaces current functionality
   - Follows established component patterns and import aliases
   - Respects the UI Navigation vs AI Interactions separation principle

The LIDA-ECharts Implementation Plan serves as the architectural blueprint for this project. All features must align with its vision of gradual enhancement while preserving existing functionality.

### Testing Commands
- Run tests: `npm run test` (verify if available in package.json)
- Run linting: `npm run lint` (verify if available in package.json)
- Run type checking: `npm run typecheck` (verify if available in package.json)

### Architecture Notes
- Backend: FastAPI with AG-UI protocol and Pydantic AI agents
- Frontend: Next.js App Router with sophisticated ECharts integration
- Data: FOCUS v1.2 compliant FinOps analytics
- Intelligence: LIDA-enhanced semantic understanding with persona-aware visualization selection

### Data Assistant Communication Protocol

**CRITICAL PRINCIPLE**: Separate UI navigation from AI interactions to avoid unnecessary LLM invocations and ensure immediate UI responsiveness.

#### UI Navigation (Direct Context Updates - No LLM)
Use **direct context updates** for immediate UI state changes:

- **Dashboard item clicks**: Show/hide Data Assistant panel sections
- **Dashboard title clicks**: Switch between Dashboard Properties view
- **Dashboard preview clicks**: Show Add Items and Dashboard Settings
- **Mode changes**: Enter/exit edit mode
- **Panel navigation**: Switch between different assistant panel views

```typescript
// ✅ CORRECT - Direct context updates for UI navigation (No LLM)
onClick={() => setActiveSection("dashboard-title")}
onClick={() => setActiveSection("dashboard-preview")}
onClick={() => { setSelectedItemId(itemId); setActiveSection("item-properties"); }}
onClick={() => { setActiveSection(null); setSelectedItemId(null); }}
```

#### AI Interactions (AgUI Protocol - With LLM)
Use **AgUI protocol** only for actions requiring AI processing:

- **Save/Reset operations**: Actual data persistence and validation
- **Content editing**: Dashboard name, description, item properties changes
- **Item creation**: Adding new dashboard components
- **Settings changes**: Grid layout, dashboard configuration
- **Conversational queries**: User asking questions about data

```typescript
// ✅ CORRECT - AgUI protocol for AI-powered actions
onClick={() => sendMessage("Save all dashboard changes")}
onClick={() => sendMessage("Reset all changes to the dashboard")}
onClick={() => sendMessage("Add a new Chart item to the dashboard")}
onValueChange={(value) => sendMessage(`Change dashboard grid to ${value} columns`)}
onChange={(e) => sendMessage(`Update item title to "${e.target.value}"`)}
```

#### Anti-Patterns to Avoid
```typescript
// ❌ WRONG - Using AgUI protocol for simple UI navigation (causes LLM delay)
onClick={() => sendMessage("Show dashboard properties editor in Data Assistant")}
onClick={() => sendMessage("DIRECT_UI_UPDATE:Show item properties")}

// ❌ WRONG - Direct function calls for AI-powered actions (bypasses protocol)
onClick={() => dashboardContext.onSave?.()}
onChange={(config) => onChange({...config, items: [...config.items, newItem]})}
```

This separation ensures:
- **Immediate UI feedback** for navigation actions
- **Proper AI integration** for content and data operations
- **Optimal performance** by avoiding unnecessary API calls
- **Clear architectural boundaries** between UI state and AI logic