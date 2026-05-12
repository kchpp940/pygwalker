import { makeObservable, observable, action, computed } from 'mobx';
import type { IFilterCondition, FilterLogic, IEnhancedFilterState } from '../interfaces/filter';
import { v4 as uuidv4 } from 'uuid';

class FilterStore {
    conditions: IFilterCondition[] = [];
    logic: FilterLogic = "AND";
    estimatedCount: number | null = null;
    isOpen: boolean = false;
    totalRowCount: number = 0;

    constructor() {
        makeObservable(this, {
            conditions: observable,
            logic: observable,
            estimatedCount: observable,
            isOpen: observable,
            totalRowCount: observable,
            addCondition: action,
            removeCondition: action,
            updateCondition: action,
            toggleCondition: action,
            setLogic: action,
            setEstimatedCount: action,
            toggleFilterPanel: action,
            setTotalRowCount: action,
            clearAllConditions: action,
            importFromFilterState: action,
            enabledConditions: computed,
            hasActiveFilters: computed,
        });
    }

    addCondition(condition: Omit<IFilterCondition, 'id'>) {
        this.conditions.push({
            ...condition,
            id: uuidv4()
        });
    }

    removeCondition(id: string) {
        this.conditions = this.conditions.filter(c => c.id !== id);
    }

    updateCondition(id: string, updates: Partial<IFilterCondition>) {
        const index = this.conditions.findIndex(c => c.id === id);
        if (index !== -1) {
            this.conditions[index] = { ...this.conditions[index], ...updates };
        }
    }

    toggleCondition(id: string) {
        const condition = this.conditions.find(c => c.id === id);
        if (condition) {
            condition.enabled = !condition.enabled;
        }
    }

    setLogic(logic: FilterLogic) {
        this.logic = logic;
    }

    setEstimatedCount(count: number | null) {
        this.estimatedCount = count;
    }

    toggleFilterPanel() {
        this.isOpen = !this.isOpen;
    }

    setTotalRowCount(count: number) {
        this.totalRowCount = count;
    }

    clearAllConditions() {
        this.conditions = [];
        this.estimatedCount = null;
    }

    importFromFilterState(state: IEnhancedFilterState) {
        this.conditions = state.conditions;
        this.logic = state.logic;
        this.estimatedCount = state.estimatedCount;
    }

    get enabledConditions() {
        return this.conditions.filter(c => c.enabled);
    }

    get hasActiveFilters() {
        return this.enabledConditions.length > 0;
    }

    exportToFilterState(): IEnhancedFilterState {
        return {
            conditions: this.conditions,
            logic: this.logic,
            estimatedCount: this.estimatedCount
        };
    }
}

const filterStore = new FilterStore();

export default filterStore;
