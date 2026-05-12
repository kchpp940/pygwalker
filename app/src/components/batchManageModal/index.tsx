import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { observer } from "mobx-react-lite";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    TrashIcon,
    ArrowUpIcon,
    ArrowDownIcon,
    CopyIcon,
    EditIcon,
    FolderIcon,
    ListIcon,
    ChevronUpIcon,
    ChevronDownIcon,
    ChevronLeftIcon,
    ChevronRightIcon,
} from 'lucide-react';
import type { IAppProps, IChartItem, IBatchRenameConfig } from '../../interfaces';
import { v4 as uuidv4 } from 'uuid';

interface IBatchManageModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    charts: IChartItem[];
    getCurrentSpec: () => any[];
    onUpdate: (newSpec: any[]) => void;
    props: IAppProps;
}

type BatchAction = "rename" | "copy" | "move" | "delete" | "group" | null;

const BatchManageModal: React.FC<IBatchManageModalProps> = observer((props) => {
    const { open, onOpenChange, charts, getCurrentSpec, onUpdate } = props;
    const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set());
    const [currentAction, setCurrentAction] = useState<BatchAction>(null);
    const [renamePattern, setRenamePattern] = useState<"prefix" | "suffix" | "numbered" | "replace">("numbered");
    const [renameValue, setRenameValue] = useState("Chart");
    const [renameStartIndex, setRenameStartIndex] = useState(1);
    const [renameSearchValue, setRenameSearchValue] = useState("");
    const [moveTargetIndex, setMoveTargetIndex] = useState<string>("0");
    const [moveDirection, setMoveDirection] = useState<"top" | "bottom" | "before" | "after">("top");
    const [copySuffix, setCopySuffix] = useState("Copy");
    const [groupName, setGroupName] = useState("Group");

    useEffect(() => {
        if (open) {
            setSelectedIndices(new Set());
            setCurrentAction(null);
            setRenameValue("Chart");
            setRenameStartIndex(1);
            setCopySuffix("Copy");
            setGroupName("Group");
            setMoveTargetIndex("0");
            setMoveDirection("top");
        }
    }, [open]);

    const toggleSelect = useCallback((index: number) => {
        setSelectedIndices(prev => {
            const next = new Set(prev);
            if (next.has(index)) {
                next.delete(index);
            } else {
                next.add(index);
            }
            return next;
        });
    }, []);

    const toggleSelectAll = useCallback(() => {
        if (selectedIndices.size === charts.length) {
            setSelectedIndices(new Set());
        } else {
            setSelectedIndices(new Set(charts.map(c => c.index)));
        }
    }, [charts, selectedIndices]);

    const selectedCharts = useMemo(() => {
        return charts.filter(c => selectedIndices.has(c.index));
    }, [charts, selectedIndices]);

    const sortedSelectedIndices = useMemo(() => {
        return Array.from(selectedIndices).sort((a, b) => a - b);
    }, [selectedIndices]);

    const generateNewVisId = () => {
        return `chart-${uuidv4().slice(0, 8)}`;
    };

    const performBatchRename = useCallback(() => {
        const spec = getCurrentSpec();
        const newSpec = [...spec];
        
        sortedSelectedIndices.forEach((index, i) => {
            const chart = { ...newSpec[index] };
            let newName = chart.name;
            
            switch (renamePattern) {
                case "prefix":
                    newName = `${renameValue}${newName}`;
                    break;
                case "suffix":
                    newName = `${newName}${renameValue}`;
                    break;
                case "numbered":
                    newName = `${renameValue} ${renameStartIndex + i}`;
                    break;
                case "replace":
                    newName = newName.replace(new RegExp(renameSearchValue, 'g'), renameValue);
                    break;
            }
            
            chart.name = newName;
            newSpec[index] = chart;
        });

        onUpdate(newSpec);
        setCurrentAction(null);
        setSelectedIndices(new Set());
    }, [getCurrentSpec, onUpdate, sortedSelectedIndices, renamePattern, renameValue, renameStartIndex, renameSearchValue]);

    const performBatchCopy = useCallback(() => {
        const spec = getCurrentSpec();
        const newCharts: any[] = [];
        
        sortedSelectedIndices.forEach((index) => {
            const chart = JSON.parse(JSON.stringify(spec[index]));
            chart.name = `${chart.name} ${copySuffix}`;
            chart.visId = generateNewVisId();
            newCharts.push(chart);
        });

        const lastSelectedIndex = sortedSelectedIndices[sortedSelectedIndices.length - 1];
        const newSpec = [
            ...spec.slice(0, lastSelectedIndex + 1),
            ...newCharts,
            ...spec.slice(lastSelectedIndex + 1)
        ];

        onUpdate(newSpec);
        setCurrentAction(null);
        setSelectedIndices(new Set());
    }, [getCurrentSpec, onUpdate, sortedSelectedIndices, copySuffix]);

    const performBatchMove = useCallback(() => {
        const spec = getCurrentSpec();
        const selectedItems = sortedSelectedIndices.map(i => spec[i]);
        
        const remaining = spec.filter((_, i) => !selectedIndices.has(i));
        
        let targetIdx = parseInt(moveTargetIndex);
        if (isNaN(targetIdx) || targetIdx < 0) targetIdx = 0;
        
        const adjustedTarget = moveDirection === "after" ? targetIdx + 1 : targetIdx;
        const insertIndex = Math.min(Math.max(adjustedTarget, 0), remaining.length);
        
        const newSpec = [
            ...remaining.slice(0, insertIndex),
            ...selectedItems,
            ...remaining.slice(insertIndex)
        ];

        onUpdate(newSpec);
        setCurrentAction(null);
        setSelectedIndices(new Set());
    }, [getCurrentSpec, onUpdate, sortedSelectedIndices, selectedIndices, moveDirection, moveTargetIndex]);

    const performBatchDelete = useCallback(() => {
        const spec = getCurrentSpec();
        const newSpec = spec.filter((_, i) => !selectedIndices.has(i));
        
        onUpdate(newSpec);
        setCurrentAction(null);
        setSelectedIndices(new Set());
    }, [getCurrentSpec, onUpdate, selectedIndices]);

    const performBatchGroup = useCallback(() => {
        const spec = getCurrentSpec();
        const newSpec = [...spec];
        
        sortedSelectedIndices.forEach((index, i) => {
            const chart = { ...newSpec[index] };
            chart.name = `[${groupName}] ${chart.name}`;
            newSpec[index] = chart;
        });

        onUpdate(newSpec);
        setCurrentAction(null);
        setSelectedIndices(new Set());
    }, [getCurrentSpec, onUpdate, sortedSelectedIndices, groupName]);

    const handleMoveUp = useCallback(() => {
        if (sortedSelectedIndices.length === 0 || sortedSelectedIndices[0] === 0) return;
        
        const spec = getCurrentSpec();
        const newSpec = [...spec];
        
        for (const idx of sortedSelectedIndices) {
            if (idx > 0 && !selectedIndices.has(idx - 1)) {
                [newSpec[idx - 1], newSpec[idx]] = [newSpec[idx], newSpec[idx - 1]];
            }
        }

        const newSelected = new Set(sortedSelectedIndices.map(i => Math.max(0, i - 1)));
        onUpdate(newSpec);
        setSelectedIndices(newSelected);
    }, [getCurrentSpec, onUpdate, sortedSelectedIndices, selectedIndices]);

    const handleMoveDown = useCallback(() => {
        if (sortedSelectedIndices.length === 0 || sortedSelectedIndices[sortedSelectedIndices.length - 1] === charts.length - 1) return;
        
        const spec = getCurrentSpec();
        const newSpec = [...spec];
        
        for (let i = sortedSelectedIndices.length - 1; i >= 0; i--) {
            const idx = sortedSelectedIndices[i];
            if (idx < newSpec.length - 1 && !selectedIndices.has(idx + 1)) {
                [newSpec[idx], newSpec[idx + 1]] = [newSpec[idx + 1], newSpec[idx]];
            }
        }

        const newSelected = new Set(sortedSelectedIndices.map(i => Math.min(charts.length - 1, i + 1)));
        onUpdate(newSpec);
        setSelectedIndices(newSelected);
    }, [getCurrentSpec, onUpdate, sortedSelectedIndices, selectedIndices, charts.length]);

    const renderActionPanel = () => {
        switch (currentAction) {
            case "rename":
                return (
                    <div className="space-y-4 p-4 border rounded-lg bg-muted/30">
                        <h4 className="font-semibold text-sm flex items-center gap-2">
                            <EditIcon className="h-4 w-4" />
                            Batch Rename
                        </h4>
                        <div className="space-y-3">
                            <div>
                                <label className="text-xs text-muted-foreground block mb-1">Rename Pattern</label>
                                <Select value={renamePattern} onValueChange={(v) => setRenamePattern(v as any)}>
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="numbered">Numbered (e.g., Chart 1, Chart 2)</SelectItem>
                                        <SelectItem value="prefix">Add Prefix</SelectItem>
                                        <SelectItem value="suffix">Add Suffix</SelectItem>
                                        <SelectItem value="replace">Replace Text</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            
                            {renamePattern === "replace" && (
                                <div>
                                    <label className="text-xs text-muted-foreground block mb-1">Search For</label>
                                    <Input 
                                        value={renameSearchValue} 
                                        onChange={(e) => setRenameSearchValue(e.target.value)}
                                        placeholder="Text to replace"
                                    />
                                </div>
                            )}
                            
                            {renamePattern !== "suffix" && (
                                <div>
                                    <label className="text-xs text-muted-foreground block mb-1">
                                        {renamePattern === "numbered" ? "Base Name" : renamePattern === "prefix" ? "Prefix" : "Replace With"}
                                    </label>
                                    <Input 
                                        value={renameValue} 
                                        onChange={(e) => setRenameValue(e.target.value)}
                                        placeholder={renamePattern === "numbered" ? "Chart" : "Enter text..."}
                                    />
                                </div>
                            )}
                            
                            {renamePattern === "suffix" && (
                                <div>
                                    <label className="text-xs text-muted-foreground block mb-1">Suffix</label>
                                    <Input 
                                        value={renameValue} 
                                        onChange={(e) => setRenameValue(e.target.value)}
                                        placeholder="Enter suffix..."
                                    />
                                </div>
                            )}
                            
                            {renamePattern === "numbered" && (
                                <div>
                                    <label className="text-xs text-muted-foreground block mb-1">Start Index</label>
                                    <Input 
                                        type="number"
                                        value={renameStartIndex} 
                                        onChange={(e) => setRenameStartIndex(Math.max(1, parseInt(e.target.value) || 1))}
                                        min="1"
                                    />
                                </div>
                            )}
                            
                            <DialogFooter className="gap-2 pt-2">
                                <Button variant="ghost" size="sm" onClick={() => setCurrentAction(null)}>
                                    Cancel
                                </Button>
                                <Button size="sm" onClick={performBatchRename}>
                                    Apply Rename ({selectedCharts.length} charts)
                                </Button>
                            </DialogFooter>
                        </div>
                    </div>
                );
                
            case "copy":
                return (
                    <div className="space-y-4 p-4 border rounded-lg bg-muted/30">
                        <h4 className="font-semibold text-sm flex items-center gap-2">
                            <CopyIcon className="h-4 w-4" />
                            Batch Copy
                        </h4>
                        <div className="space-y-3">
                            <div>
                                <label className="text-xs text-muted-foreground block mb-1">Copy Suffix</label>
                                <Input 
                                    value={copySuffix} 
                                    onChange={(e) => setCopySuffix(e.target.value)}
                                    placeholder="Copy"
                                />
                            </div>
                            <p className="text-xs text-muted-foreground">
                                Selected {selectedCharts.length} chart(s) will be duplicated with suffix "{copySuffix}"
                            </p>
                            <DialogFooter className="gap-2 pt-2">
                                <Button variant="ghost" size="sm" onClick={() => setCurrentAction(null)}>
                                    Cancel
                                </Button>
                                <Button size="sm" onClick={performBatchCopy}>
                                    Confirm Copy
                                </Button>
                            </DialogFooter>
                        </div>
                    </div>
                );
                
            case "move":
                return (
                    <div className="space-y-4 p-4 border rounded-lg bg-muted/30">
                        <h4 className="font-semibold text-sm flex items-center gap-2">
                            <ListIcon className="h-4 w-4" />
                            Batch Move
                        </h4>
                        <div className="space-y-3">
                            <div className="grid grid-cols-2 gap-2">
                                <Button variant="outline" size="sm" onClick={() => setMoveDirection("top")} className={moveDirection === "top" ? "border-primary" : ""}>
                                    Move to Top
                                </Button>
                                <Button variant="outline" size="sm" onClick={() => setMoveDirection("bottom")} className={moveDirection === "bottom" ? "border-primary" : ""}>
                                    Move to Bottom
                                </Button>
                                <Button variant="outline" size="sm" onClick={() => setMoveDirection("before")} className={moveDirection === "before" ? "border-primary" : ""}>
                                    Before Index
                                </Button>
                                <Button variant="outline" size="sm" onClick={() => setMoveDirection("after")} className={moveDirection === "after" ? "border-primary" : ""}>
                                    After Index
                                </Button>
                            </div>
                            
                            {(moveDirection === "before" || moveDirection === "after") && (
                                <div>
                                    <label className="text-xs text-muted-foreground block mb-1">Target Chart Index (0-based)</label>
                                    <Select value={moveTargetIndex} onValueChange={setMoveTargetIndex}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select target chart" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {charts.map((chart, idx) => (
                                                <SelectItem key={idx} value={idx.toString()}>
                                                    #{idx} - {chart.name}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                            )}
                            
                            <DialogFooter className="gap-2 pt-2">
                                <Button variant="ghost" size="sm" onClick={() => setCurrentAction(null)}>
                                    Cancel
                                </Button>
                                <Button size="sm" onClick={performBatchMove}>
                                    Confirm Move ({selectedCharts.length} charts)
                                </Button>
                            </DialogFooter>
                        </div>
                    </div>
                );
                
            case "delete":
                return (
                    <div className="space-y-4 p-4 border rounded-lg bg-destructive/10">
                        <h4 className="font-semibold text-sm flex items-center gap-2 text-destructive">
                            <TrashIcon className="h-4 w-4" />
                            Batch Delete
                        </h4>
                        <p className="text-sm text-muted-foreground">
                            Are you sure you want to delete <strong>{selectedCharts.length}</strong> chart(s)? This action cannot be undone.
                        </p>
                        <ul className="text-xs text-muted-foreground space-y-1 max-h-32 overflow-y-auto">
                            {selectedCharts.map(chart => (
                                <li key={chart.index}>• {chart.name}</li>
                            ))}
                        </ul>
                        <DialogFooter className="gap-2 pt-2">
                            <Button variant="ghost" size="sm" onClick={() => setCurrentAction(null)}>
                                Cancel
                            </Button>
                            <Button variant="destructive" size="sm" onClick={performBatchDelete}>
                                Confirm Delete
                            </Button>
                        </DialogFooter>
                    </div>
                );
                
            case "group":
                return (
                    <div className="space-y-4 p-4 border rounded-lg bg-muted/30">
                        <h4 className="font-semibold text-sm flex items-center gap-2">
                            <FolderIcon className="h-4 w-4" />
                            Batch Group
                        </h4>
                        <div className="space-y-3">
                            <div>
                                <label className="text-xs text-muted-foreground block mb-1">Group Name Prefix</label>
                                <Input 
                                    value={groupName} 
                                    onChange={(e) => setGroupName(e.target.value)}
                                    placeholder="Group"
                                />
                            </div>
                            <p className="text-xs text-muted-foreground">
                                Selected chart names will be prefixed with [{groupName}]
                            </p>
                            <DialogFooter className="gap-2 pt-2">
                                <Button variant="ghost" size="sm" onClick={() => setCurrentAction(null)}>
                                    Cancel
                                </Button>
                                <Button size="sm" onClick={performBatchGroup}>
                                    Apply Group
                                </Button>
                            </DialogFooter>
                        </div>
                    </div>
                );
                
            default:
                return null;
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl max-h-[85vh] flex flex-col">
                <DialogHeader>
                    <DialogTitle>Batch Chart Management</DialogTitle>
                    <DialogDescription>
                        Select charts and apply batch operations. {selectedIndices.size} of {charts.length} selected.
                    </DialogDescription>
                </DialogHeader>

                <div className="flex-1 space-y-4 overflow-hidden flex flex-col">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Checkbox 
                                checked={selectedIndices.size === charts.length && charts.length > 0}
                                onCheckedChange={toggleSelectAll}
                            />
                            <span className="text-sm">Select All</span>
                        </div>
                        
                        <div className="flex items-center gap-1">
                            <Button 
                                variant="outline" 
                                size="icon" 
                                onClick={handleMoveUp}
                                disabled={selectedIndices.size === 0}
                                title="Move Up"
                            >
                                <ChevronUpIcon className="h-4 w-4" />
                            </Button>
                            <Button 
                                variant="outline" 
                                size="icon" 
                                onClick={handleMoveDown}
                                disabled={selectedIndices.size === 0}
                                title="Move Down"
                            >
                                <ChevronDownIcon className="h-4 w-4" />
                            </Button>
                        </div>
                    </div>

                    <div className="border rounded-lg flex-1 overflow-y-auto">
                        <div className="divide-y">
                            {charts.map((chart) => (
                                <div 
                                    key={chart.index}
                                    className={`flex items-center gap-3 p-3 hover:bg-muted/50 cursor-pointer transition-colors ${selectedIndices.has(chart.index) ? 'bg-primary/5' : ''}`}
                                    onClick={() => toggleSelect(chart.index)}
                                >
                                    <Checkbox 
                                        checked={selectedIndices.has(chart.index)}
                                        onCheckedChange={() => toggleSelect(chart.index)}
                                        onClick={(e) => e.stopPropagation()}
                                    />
                                    <span className="text-xs text-muted-foreground w-8 text-right">
                                        #{chart.index}
                                    </span>
                                    <span className="text-sm flex-1 truncate">
                                        {chart.name}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="flex flex-wrap gap-2 pt-2">
                        <Button 
                            variant="outline" 
                            size="sm"
                            disabled={selectedIndices.size === 0}
                            onClick={() => setCurrentAction("rename")}
                            className="flex items-center gap-1"
                        >
                            <EditIcon className="h-4 w-4" />
                            Rename
                        </Button>
                        <Button 
                            variant="outline" 
                            size="sm"
                            disabled={selectedIndices.size === 0}
                            onClick={() => setCurrentAction("copy")}
                            className="flex items-center gap-1"
                        >
                            <CopyIcon className="h-4 w-4" />
                            Copy
                        </Button>
                        <Button 
                            variant="outline" 
                            size="sm"
                            disabled={selectedIndices.size === 0}
                            onClick={() => setCurrentAction("move")}
                            className="flex items-center gap-1"
                        >
                            <ListIcon className="h-4 w-4" />
                            Move
                        </Button>
                        <Button 
                            variant="outline" 
                            size="sm"
                            disabled={selectedIndices.size === 0}
                            onClick={() => setCurrentAction("group")}
                            className="flex items-center gap-1"
                        >
                            <FolderIcon className="h-4 w-4" />
                            Group
                        </Button>
                        <Button 
                            variant="destructive" 
                            size="sm"
                            disabled={selectedIndices.size === 0}
                            onClick={() => setCurrentAction("delete")}
                            className="flex items-center gap-1 ml-auto"
                        >
                            <TrashIcon className="h-4 w-4" />
                            Delete
                        </Button>
                    </div>

                    {currentAction && renderActionPanel()}
                </div>

                <DialogFooter>
                    <Button onClick={() => onOpenChange(false)}>
                        Done
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
});

export default BatchManageModal;
