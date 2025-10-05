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
**IMPORTANT**: The Data Assistant panel must ALWAYS use the AgUI protocol for all communication with the rest of the frontend application.

- **Use `sendMessage()` for all actions**: Reset, Save, and any dashboard operations
- **NO direct function calls**: Avoid calling dashboard functions directly from Data Assistant
- **Maintain architectural boundaries**: Data Assistant stays within AgUI communication layer
- **Protocol compliance**: All assistant actions go through established AgUI message system

**Examples:**
```typescript
// ✅ CORRECT - Use AgUI protocol for actions
onClick={() => sendMessage("Save all dashboard changes")}
onClick={() => sendMessage("Reset all changes to the dashboard")}

// ✅ CORRECT - Use AgUI protocol for navigation
onClick={() => sendMessage("Show dashboard properties editor in Data Assistant")}
onClick={() => sendMessage("Show dashboard editor tools in Data Assistant")}
onClick={() => sendMessage("Switch to default Data Assistant view")}

// ✅ CORRECT - Use AgUI protocol for dashboard editing
onClick={() => sendMessage("Add a new Chart item to the dashboard")}
onValueChange={(value) => sendMessage(`Change dashboard grid to ${value} columns`)}
onChange={(e) => sendMessage(`Change dashboard name to "${e.target.value}"`)}

// ❌ INCORRECT - Direct function calls
onClick={() => dashboardContext.onSave?.()}
onClick={() => setActiveSection("dashboard-title")}
onClick={() => addItem(itemType.value)}
onChange={(config) => onChange({...config, items: [...config.items, newItem]})}
```

This ensures proper separation of concerns and maintains consistency with the AgUI communication architecture.