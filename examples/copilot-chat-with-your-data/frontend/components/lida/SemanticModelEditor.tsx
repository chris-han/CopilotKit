"use client";

import { useState, useCallback, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import { Badge } from "../ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../ui/dialog";
import {
  Plus,
  Edit,
  Trash2,
  Save,
  Database,
  Link,
  TrendingUp,
  GitBranch,
  AlertCircle
} from "lucide-react";

interface SemanticEntity {
  name: string;
  description: string;
  primary_key: string;
  attributes: string[];
  relationships: string[];
}

interface SemanticMetric {
  name: string;
  description: string;
  type: string;
  base_field: string;
  sql: string;
  dimensions: string[];
  filters: string[];
}

interface SemanticModel {
  name: string;
  entities: SemanticEntity[];
  metrics: SemanticMetric[];
  relationships: any[];
}

interface SemanticModelEditorProps {
  modelName: string;
  onModelChange?: (model: SemanticModel) => void;
  readOnly?: boolean;
}

export function SemanticModelEditor({
  modelName,
  onModelChange,
  readOnly = false
}: SemanticModelEditorProps) {
  const [model, setModel] = useState<SemanticModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingEntity, setEditingEntity] = useState<SemanticEntity | null>(null);
  const [editingMetric, setEditingMetric] = useState<SemanticMetric | null>(null);
  const [isEntityDialogOpen, setIsEntityDialogOpen] = useState(false);
  const [isMetricDialogOpen, setIsMetricDialogOpen] = useState(false);

  // Load semantic model
  const loadModel = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`http://localhost:8004/semantic-model/${modelName}`);
      if (!response.ok) {
        if (response.status === 404) {
          // Create new model structure if not found
          const newModel: SemanticModel = {
            name: modelName,
            entities: [],
            metrics: [],
            relationships: []
          };
          setModel(newModel);
          return;
        }
        throw new Error(`Failed to load model: ${response.statusText}`);
      }

      const modelData = await response.json();
      setModel(modelData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load semantic model');
    } finally {
      setLoading(false);
    }
  }, [modelName]);

  useEffect(() => {
    loadModel();
  }, [loadModel]);

  // Handle model changes
  const handleModelUpdate = useCallback((updatedModel: SemanticModel) => {
    setModel(updatedModel);
    onModelChange?.(updatedModel);
  }, [onModelChange]);

  // Entity management
  const handleAddEntity = useCallback(() => {
    setEditingEntity({
      name: '',
      description: '',
      primary_key: '',
      attributes: [],
      relationships: []
    });
    setIsEntityDialogOpen(true);
  }, []);

  const handleEditEntity = useCallback((entity: SemanticEntity) => {
    setEditingEntity(entity);
    setIsEntityDialogOpen(true);
  }, []);

  const handleSaveEntity = useCallback((entity: SemanticEntity) => {
    if (!model) return;

    const updatedEntities = editingEntity && model.entities.includes(editingEntity)
      ? model.entities.map(e => e === editingEntity ? entity : e)
      : [...model.entities, entity];

    const updatedModel = { ...model, entities: updatedEntities };
    handleModelUpdate(updatedModel);
    setIsEntityDialogOpen(false);
    setEditingEntity(null);
  }, [model, editingEntity, handleModelUpdate]);

  const handleDeleteEntity = useCallback((entity: SemanticEntity) => {
    if (!model) return;

    const updatedEntities = model.entities.filter(e => e !== entity);
    const updatedModel = { ...model, entities: updatedEntities };
    handleModelUpdate(updatedModel);
  }, [model, handleModelUpdate]);

  // Metric management
  const handleAddMetric = useCallback(() => {
    setEditingMetric({
      name: '',
      description: '',
      type: 'sum',
      base_field: '',
      sql: '',
      dimensions: [],
      filters: []
    });
    setIsMetricDialogOpen(true);
  }, []);

  const handleEditMetric = useCallback((metric: SemanticMetric) => {
    setEditingMetric(metric);
    setIsMetricDialogOpen(true);
  }, []);

  const handleSaveMetric = useCallback((metric: SemanticMetric) => {
    if (!model) return;

    const updatedMetrics = editingMetric && model.metrics.includes(editingMetric)
      ? model.metrics.map(m => m === editingMetric ? metric : m)
      : [...model.metrics, metric];

    const updatedModel = { ...model, metrics: updatedMetrics };
    handleModelUpdate(updatedModel);
    setIsMetricDialogOpen(false);
    setEditingMetric(null);
  }, [model, editingMetric, handleModelUpdate]);

  const handleDeleteMetric = useCallback((metric: SemanticMetric) => {
    if (!model) return;

    const updatedMetrics = model.metrics.filter(m => m !== metric);
    const updatedModel = { ...model, metrics: updatedMetrics };
    handleModelUpdate(updatedModel);
  }, [model, handleModelUpdate]);

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <span className="ml-2">Loading semantic model...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center text-red-600">
            <AlertCircle className="h-5 w-5 mr-2" />
            <span>{error}</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!model) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">
            No semantic model found
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Model Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Database className="h-5 w-5" />
            <span>Semantic Model: {model.name}</span>
          </CardTitle>
          <CardDescription>
            Define business entities, metrics, and relationships for your data model
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Model Content */}
      <Tabs defaultValue="entities" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="entities">
            Entities ({model?.entities?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="metrics">
            Metrics ({model?.metrics?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="relationships">
            Relationships ({model?.relationships?.length || 0})
          </TabsTrigger>
        </TabsList>

        {/* Entities Tab */}
        <TabsContent value="entities" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Business Entities</h3>
            {!readOnly && (
              <Button onClick={handleAddEntity} size="sm">
                <Plus className="h-4 w-4 mr-2" />
                Add Entity
              </Button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {(model?.entities || []).map((entity, index) => (
              <Card key={index}>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-base">{entity.name}</CardTitle>
                      <CardDescription className="text-sm">
                        {entity.description}
                      </CardDescription>
                    </div>
                    {!readOnly && (
                      <div className="flex space-x-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEditEntity(entity)}
                        >
                          <Edit className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteEntity(entity)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="space-y-2">
                    <div>
                      <Label className="text-xs font-medium">Primary Key</Label>
                      <p className="text-xs text-muted-foreground">{entity.primary_key}</p>
                    </div>
                    <div>
                      <Label className="text-xs font-medium">Attributes ({entity.attributes?.length || 0})</Label>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {(entity.attributes || []).slice(0, 3).map((attr, i) => (
                          <Badge key={i} variant="secondary" className="text-xs">
                            {attr}
                          </Badge>
                        ))}
                        {(entity.attributes?.length || 0) > 3 && (
                          <Badge variant="outline" className="text-xs">
                            +{(entity.attributes?.length || 0) - 3} more
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Metrics Tab */}
        <TabsContent value="metrics" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Business Metrics</h3>
            {!readOnly && (
              <Button onClick={handleAddMetric} size="sm">
                <Plus className="h-4 w-4 mr-2" />
                Add Metric
              </Button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {(model?.metrics || []).map((metric, index) => (
              <Card key={index}>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-base flex items-center">
                        <TrendingUp className="h-4 w-4 mr-2" />
                        {metric.name}
                      </CardTitle>
                      <CardDescription className="text-sm">
                        {metric.description}
                      </CardDescription>
                    </div>
                    {!readOnly && (
                      <div className="flex space-x-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEditMetric(metric)}
                        >
                          <Edit className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteMetric(metric)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="space-y-2">
                    <div>
                      <Label className="text-xs font-medium">Type</Label>
                      <Badge variant="outline" className="text-xs ml-2">
                        {metric.type}
                      </Badge>
                    </div>
                    <div>
                      <Label className="text-xs font-medium">Base Field</Label>
                      <p className="text-xs text-muted-foreground">{metric.base_field}</p>
                    </div>
                    <div>
                      <Label className="text-xs font-medium">Dimensions ({metric.dimensions?.length || 0})</Label>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {(metric.dimensions || []).slice(0, 2).map((dim, i) => (
                          <Badge key={i} variant="secondary" className="text-xs">
                            {dim}
                          </Badge>
                        ))}
                        {(metric.dimensions?.length || 0) > 2 && (
                          <Badge variant="outline" className="text-xs">
                            +{(metric.dimensions?.length || 0) - 2} more
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Relationships Tab */}
        <TabsContent value="relationships" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Entity Relationships</h3>
            {!readOnly && (
              <Button size="sm">
                <Link className="h-4 w-4 mr-2" />
                Add Relationship
              </Button>
            )}
          </div>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-center text-muted-foreground">
                <GitBranch className="h-8 w-8 mr-2" />
                <span>Relationship visualization will be shown here</span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Entity Dialog */}
      <Dialog open={isEntityDialogOpen} onOpenChange={setIsEntityDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {editingEntity && model?.entities?.includes(editingEntity) ? 'Edit' : 'Add'} Entity
            </DialogTitle>
          </DialogHeader>
          <EntityForm
            entity={editingEntity}
            onSave={handleSaveEntity}
            onCancel={() => setIsEntityDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Metric Dialog */}
      <Dialog open={isMetricDialogOpen} onOpenChange={setIsMetricDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {editingMetric && model?.metrics?.includes(editingMetric) ? 'Edit' : 'Add'} Metric
            </DialogTitle>
          </DialogHeader>
          <MetricForm
            metric={editingMetric}
            onSave={handleSaveMetric}
            onCancel={() => setIsMetricDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Entity Form Component
function EntityForm({
  entity,
  onSave,
  onCancel
}: {
  entity: SemanticEntity | null;
  onSave: (entity: SemanticEntity) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState<SemanticEntity>(
    entity || {
      name: '',
      description: '',
      primary_key: '',
      attributes: [],
      relationships: []
    }
  );

  const [attributeInput, setAttributeInput] = useState('');

  const handleAddAttribute = () => {
    if (attributeInput.trim() && !formData.attributes.includes(attributeInput.trim())) {
      setFormData(prev => ({
        ...prev,
        attributes: [...prev.attributes, attributeInput.trim()]
      }));
      setAttributeInput('');
    }
  };

  const handleRemoveAttribute = (attr: string) => {
    setFormData(prev => ({
      ...prev,
      attributes: prev.attributes.filter(a => a !== attr)
    }));
  };

  const handleSave = () => {
    if (formData.name.trim()) {
      onSave(formData);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <Label htmlFor="entity-name">Name</Label>
        <Input
          id="entity-name"
          value={formData.name}
          onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
          placeholder="e.g., Customer, Order, Product"
        />
      </div>

      <div>
        <Label htmlFor="entity-description">Description</Label>
        <Textarea
          id="entity-description"
          value={formData.description}
          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
          placeholder="Describe this business entity..."
        />
      </div>

      <div>
        <Label htmlFor="entity-primary-key">Primary Key</Label>
        <Input
          id="entity-primary-key"
          value={formData.primary_key}
          onChange={(e) => setFormData(prev => ({ ...prev, primary_key: e.target.value }))}
          placeholder="e.g., customer_id, order_id"
        />
      </div>

      <div>
        <Label>Attributes</Label>
        <div className="flex space-x-2 mt-1">
          <Input
            value={attributeInput}
            onChange={(e) => setAttributeInput(e.target.value)}
            placeholder="Add attribute..."
            onKeyPress={(e) => e.key === 'Enter' && handleAddAttribute()}
          />
          <Button onClick={handleAddAttribute} size="sm">
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex flex-wrap gap-2 mt-2">
          {formData.attributes.map((attr, i) => (
            <Badge key={i} variant="secondary" className="cursor-pointer">
              {attr}
              <button
                onClick={() => handleRemoveAttribute(attr)}
                className="ml-2 hover:text-red-500"
              >
                ×
              </button>
            </Badge>
          ))}
        </div>
      </div>

      <div className="flex justify-end space-x-2 pt-4">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button onClick={handleSave}>
          <Save className="h-4 w-4 mr-2" />
          Save Entity
        </Button>
      </div>
    </div>
  );
}

// Metric Form Component
function MetricForm({
  metric,
  onSave,
  onCancel
}: {
  metric: SemanticMetric | null;
  onSave: (metric: SemanticMetric) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState<SemanticMetric>(
    metric || {
      name: '',
      description: '',
      type: 'sum',
      base_field: '',
      sql: '',
      dimensions: [],
      filters: []
    }
  );

  const [dimensionInput, setDimensionInput] = useState('');

  const handleAddDimension = () => {
    if (dimensionInput.trim() && !formData.dimensions.includes(dimensionInput.trim())) {
      setFormData(prev => ({
        ...prev,
        dimensions: [...prev.dimensions, dimensionInput.trim()]
      }));
      setDimensionInput('');
    }
  };

  const handleRemoveDimension = (dim: string) => {
    setFormData(prev => ({
      ...prev,
      dimensions: prev.dimensions.filter(d => d !== dim)
    }));
  };

  const handleSave = () => {
    if (formData.name.trim()) {
      onSave(formData);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="metric-name">Name</Label>
          <Input
            id="metric-name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            placeholder="e.g., Total Revenue, Customer Count"
          />
        </div>
        <div>
          <Label htmlFor="metric-type">Type</Label>
          <select
            id="metric-type"
            value={formData.type}
            onChange={(e) => setFormData(prev => ({ ...prev, type: e.target.value }))}
            className="w-full p-2 border rounded-md"
          >
            <option value="sum">Sum</option>
            <option value="count">Count</option>
            <option value="avg">Average</option>
            <option value="min">Minimum</option>
            <option value="max">Maximum</option>
          </select>
        </div>
      </div>

      <div>
        <Label htmlFor="metric-description">Description</Label>
        <Textarea
          id="metric-description"
          value={formData.description}
          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
          placeholder="Describe this business metric..."
        />
      </div>

      <div>
        <Label htmlFor="metric-base-field">Base Field</Label>
        <Input
          id="metric-base-field"
          value={formData.base_field}
          onChange={(e) => setFormData(prev => ({ ...prev, base_field: e.target.value }))}
          placeholder="e.g., amount, quantity, customer_id"
        />
      </div>

      <div>
        <Label htmlFor="metric-sql">SQL Expression</Label>
        <Textarea
          id="metric-sql"
          value={formData.sql}
          onChange={(e) => setFormData(prev => ({ ...prev, sql: e.target.value }))}
          placeholder="SUM(amount) or COUNT(DISTINCT customer_id)"
          className="font-mono text-sm"
        />
      </div>

      <div>
        <Label>Dimensions</Label>
        <div className="flex space-x-2 mt-1">
          <Input
            value={dimensionInput}
            onChange={(e) => setDimensionInput(e.target.value)}
            placeholder="Add dimension..."
            onKeyPress={(e) => e.key === 'Enter' && handleAddDimension()}
          />
          <Button onClick={handleAddDimension} size="sm">
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex flex-wrap gap-2 mt-2">
          {formData.dimensions.map((dim, i) => (
            <Badge key={i} variant="secondary" className="cursor-pointer">
              {dim}
              <button
                onClick={() => handleRemoveDimension(dim)}
                className="ml-2 hover:text-red-500"
              >
                ×
              </button>
            </Badge>
          ))}
        </div>
      </div>

      <div className="flex justify-end space-x-2 pt-4">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button onClick={handleSave}>
          <Save className="h-4 w-4 mr-2" />
          Save Metric
        </Button>
      </div>
    </div>
  );
}