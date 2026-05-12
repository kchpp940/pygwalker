import React, { useState, useCallback, useEffect } from "react";
import { observer } from "mobx-react-lite";
import { XIcon, PlusIcon, Trash2Icon, FilterIcon, EyeIcon, EyeOffIcon } from "lucide-react";
import filterStore from "../../store/filter";
import {
    getConditionTypeByFieldType,
    getDefaultValueForConditionType,
    estimateFilteredCount,
    getFieldUniqueValues,
    getFieldRange
} from "../../utils/filter";
import type { IFilterCondition, FilterConditionType, IFieldMeta } from "../../interfaces/filter";
import type { IRow } from '@kanaries/graphic-walker/interfaces';

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

interface IEnhancedFilterProps {
    fields: IFieldMeta[];
    dataSource: IRow[];
    onApply?: () => void;
}

const EnhancedFilterPanel: React.FC<IEnhancedFilterProps> = observer((props) => {
    const { fields, dataSource, onApply } = props;

    useEffect(() => {
        if (dataSource.length > 0) {
            filterStore.setTotalRowCount(dataSource.length);
        }
    }, [dataSource.length]);

    useEffect(() => {
        if (dataSource.length > 0 && filterStore.hasActiveFilters) {
            const count = estimateFilteredCount(
                dataSource,
                filterStore.conditions,
                filterStore.logic
            );
            filterStore.setEstimatedCount(count);
        } else {
            filterStore.setEstimatedCount(null);
        }
    }, [filterStore.conditions, filterStore.logic, dataSource]);

    const handleAddCondition = useCallback(() => {
        if (fields.length === 0) return;
        
        const firstField = fields[0];
        const conditionTypes = getConditionTypeByFieldType(firstField.semanticType);
        
        filterStore.addCondition({
            fid: firstField.fid,
            fieldName: firstField.name,
            fieldType: firstField.semanticType === "quantitative" ? "measure" : "dimension",
            conditionType: conditionTypes[0],
            value: getDefaultValueForConditionType(conditionTypes[0]),
            enabled: true
        });
    }, [fields]);

    const handleFieldChange = useCallback((id: string, fid: string) => {
        const field = fields.find(f => f.fid === fid);
        if (!field) return;
        
        const conditionTypes = getConditionTypeByFieldType(field.semanticType);
        filterStore.updateCondition(id, {
            fid,
            fieldName: field.name,
            fieldType: field.semanticType === "quantitative" ? "measure" : "dimension",
            conditionType: conditionTypes[0],
            value: getDefaultValueForConditionType(conditionTypes[0])
        });
    }, [fields]);

    const handleConditionTypeChange = useCallback((id: string, conditionType: FilterConditionType) => {
        filterStore.updateCondition(id, {
            conditionType,
            value: getDefaultValueForConditionType(conditionType)
        });
    }, []);

    const renderValueEditor = useCallback((condition: IFilterCondition) => {
        const field = fields.find(f => f.fid === condition.fid);
        if (!field) return null;

        switch (condition.conditionType) {
            case "range":
            case "temporal range": {
                const range = getFieldRange(dataSource, condition.fid);
                const [min, max] = condition.value || [null, null];
                return (
                    <div className="flex gap-2 items-center">
                        <Input
                            type="number"
                            placeholder={range ? `Min (${range[0]})` : "Min"}
                            value={min ?? ""}
                            onChange={(e) => {
                                const newValue = [...(condition.value || [null, null])];
                                newValue[0] = e.target.value === "" ? null : Number(e.target.value);
                                filterStore.updateCondition(condition.id, { value: newValue });
                            }}
                            className="w-28"
                        />
                        <span className="text-muted-foreground">to</span>
                        <Input
                            type="number"
                            placeholder={range ? `Max (${range[1]})` : "Max"}
                            value={max ?? ""}
                            onChange={(e) => {
                                const newValue = [...(condition.value || [null, null])];
                                newValue[1] = e.target.value === "" ? null : Number(e.target.value);
                                filterStore.updateCondition(condition.id, { value: newValue });
                            }}
                            className="w-28"
                        />
                    </div>
                );
            }
            case "one of":
            case "not in": {
                const uniqueValues = getFieldUniqueValues(dataSource, condition.fid);
                const selectedValues = condition.value || [];
                return (
                    <div className="max-h-40 overflow-y-auto border rounded-md p-2">
                        {uniqueValues.map((value, idx) => (
                            <div key={idx} className="flex items-center gap-2 py-1">
                                <Checkbox
                                    checked={selectedValues.includes(value)}
                                    onCheckedChange={(checked) => {
                                        let newValue: any[];
                                        if (checked) {
                                            newValue = [...selectedValues, value];
                                        } else {
                                            newValue = selectedValues.filter((v: any) => v !== value);
                                        }
                                        filterStore.updateCondition(condition.id, { value: newValue });
                                    }}
                                />
                                <Label className="text-sm cursor-pointer">{String(value)}</Label>
                            </div>
                        ))}
                    </div>
                );
            }
            case "contains":
                return (
                    <Input
                        type="text"
                        placeholder="Contains text..."
                        value={condition.value || ""}
                        onChange={(e) => filterStore.updateCondition(condition.id, { value: e.target.value })}
                    />
                );
            case "equals":
                return (
                    <Input
                        type="text"
                        placeholder="Equals..."
                        value={condition.value ?? ""}
                        onChange={(e) => filterStore.updateCondition(condition.id, { value: e.target.value })}
                    />
                );
            case "greater than":
                return (
                    <Input
                        type="number"
                        placeholder="Greater than..."
                        value={condition.value ?? ""}
                        onChange={(e) => filterStore.updateCondition(condition.id, { value: e.target.value === "" ? null : Number(e.target.value) })}
                    />
                );
            case "less than":
                return (
                    <Input
                        type="number"
                        placeholder="Less than..."
                        value={condition.value ?? ""}
                        onChange={(e) => filterStore.updateCondition(condition.id, { value: e.target.value === "" ? null : Number(e.target.value) })}
                    />
                );
            default:
                return null;
        }
    }, [fields, dataSource]);

    const handleApply = useCallback(() => {
        if (onApply) {
            onApply();
        }
        filterStore.toggleFilterPanel();
    }, [onApply]);

    return (
        <Dialog open={filterStore.isOpen} onOpenChange={(open) => !open && filterStore.toggleFilterPanel()}>
            <DialogContent className="sm:max-w-[700px] max-h-[85vh] overflow-hidden flex flex-col">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <FilterIcon className="h-5 w-5" />
                        Enhanced Filter
                    </DialogTitle>
                    <DialogDescription>
                        Add multiple filter conditions and apply them to your chart.
                    </DialogDescription>
                </DialogHeader>

                <div className="flex-1 overflow-y-auto space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <Label>Logic:</Label>
                            <ToggleGroup type="single" value={filterStore.logic} onValueChange={(value) => value && filterStore.setLogic(value as any)}>
                                <ToggleGroupItem value="AND">AND</ToggleGroupItem>
                                <ToggleGroupItem value="OR">OR</ToggleGroupItem>
                            </ToggleGroup>
                        </div>
                        
                        <div className="text-sm text-muted-foreground">
                            {filterStore.estimatedCount !== null ? (
                                <span>
                                    <span className="font-medium text-foreground">{filterStore.estimatedCount}</span> of {filterStore.totalRowCount} rows selected
                                    {filterStore.totalRowCount > 0 && (
                                        <span className="ml-2">
                                            ({((filterStore.estimatedCount / filterStore.totalRowCount) * 100).toFixed(1)}%)
                                        </span>
                                    )}
                                </span>
                            ) : filterStore.totalRowCount > 0 ? (
                                <span>Total: {filterStore.totalRowCount} rows</span>
                            ) : null}
                        </div>
                    </div>

                    {filterStore.conditions.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground border-2 border-dashed rounded-lg">
                            <p>No filter conditions yet</p>
                            <p className="text-sm mt-1">Click the button below to add a condition</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {filterStore.conditions.map((condition, index) => {
                                const field = fields.find(f => f.fid === condition.fid);
                                const conditionTypes = field ? getConditionTypeByFieldType(field.semanticType) : [];
                                
                                return (
                                    <div 
                                        key={condition.id} 
                                        className={`p-4 border rounded-lg space-y-3 transition-opacity ${!condition.enabled ? 'opacity-50' : ''}`}
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <span className="text-sm font-medium text-muted-foreground">
                                                    Condition {index + 1}
                                                </span>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    onClick={() => filterStore.toggleCondition(condition.id)}
                                                    title={condition.enabled ? "Disable" : "Enable"}
                                                >
                                                    {condition.enabled ? 
                                                        <EyeIcon className="h-4 w-4" /> : 
                                                        <EyeOffIcon className="h-4 w-4" />
                                                    }
                                                </Button>
                                            </div>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => filterStore.removeCondition(condition.id)}
                                                title="Remove"
                                            >
                                                <Trash2Icon className="h-4 w-4 text-red-500" />
                                            </Button>
                                        </div>
                                        
                                        <div className="flex flex-wrap items-center gap-2">
                                            <Select
                                                value={condition.fid}
                                                onValueChange={(value) => handleFieldChange(condition.id, value)}
                                            >
                                                <SelectTrigger className="w-32">
                                                    <SelectValue placeholder="Field" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {fields.map((f) => (
                                                        <SelectItem key={f.fid} value={f.fid}>
                                                            {f.name}
                                                        </SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>

                                            <Select
                                                value={condition.conditionType}
                                                onValueChange={(value) => handleConditionTypeChange(condition.id, value as FilterConditionType)}
                                            >
                                                <SelectTrigger className="w-32">
                                                    <SelectValue placeholder="Condition" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {conditionTypes.map((type) => (
                                                        <SelectItem key={type} value={type}>
                                                            {type}
                                                        </SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                        </div>

                                        <div className="pt-2">
                                            {renderValueEditor(condition)}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    <Button
                        variant="outline"
                        onClick={handleAddCondition}
                        className="w-full"
                        disabled={fields.length === 0}
                    >
                        <PlusIcon className="h-4 w-4 mr-2" />
                        Add Condition
                    </Button>
                </div>

                <div className="flex justify-between pt-4 border-t">
                    <Button
                        variant="outline"
                        onClick={() => filterStore.clearAllConditions()}
                        disabled={filterStore.conditions.length === 0}
                    >
                        Clear All
                    </Button>
                    <div className="flex gap-2">
                        <Button variant="outline" onClick={() => filterStore.toggleFilterPanel()}>
                            Cancel
                        </Button>
                        <Button onClick={handleApply}>
                            Apply Filters
                        </Button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
});

export default EnhancedFilterPanel;
