import { VegaliteMapper } from '@kanaries/graphic-walker/lib/vl2gw';


function isGwChartConfig(configItem: any): boolean {
    return ["config", "encodings", "visId"].every(key => 
        Object.prototype.hasOwnProperty.call(configItem, key)
    );
}


function convertVegaToGw(
    vegaSpec: any, 
    fields: any[], 
    index: number
): any {
    const randomId = Math.random().toString(16).split(".").at(1) || `chart_${index}`;
    return VegaliteMapper(
        vegaSpec, 
        fields, 
        randomId, 
        `Chart ${index + 1}`
    );
}


export default function formatSpec(spec: any[], fields: any[]): any[] {
    return spec.map((item, index) => {
        if (isGwChartConfig(item)) {
            return item;
        }
        return convertVegaToGw(item, fields, index);
    });
}


export function validateSpecFormat(spec: any): {
    isValid: boolean;
    format: 'gw' | 'vega' | 'mixed' | 'empty' | 'unknown';
    items: number;
} {
    if (!spec || !Array.isArray(spec)) {
        return { isValid: false, format: 'unknown', items: 0 };
    }
    
    if (spec.length === 0) {
        return { isValid: true, format: 'empty', items: 0 };
    }
    
    let gwCount = 0;
    let vegaCount = 0;
    
    for (const item of spec) {
        if (isGwChartConfig(item)) {
            gwCount++;
        } else {
            vegaCount++;
        }
    }
    
    if (gwCount === spec.length) {
        return { isValid: true, format: 'gw', items: spec.length };
    }
    
    if (vegaCount === spec.length) {
        return { isValid: true, format: 'vega', items: spec.length };
    }
    
    return { isValid: true, format: 'mixed', items: spec.length };
}
