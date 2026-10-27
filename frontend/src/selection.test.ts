import {expect,it} from 'vitest';
import {toggleChild,selectionState} from './selection';
it('parent selection transitions through partial and all including unclassified',()=>{const all=['X','Y',null];expect(selectionState(undefined,all)).toBe('none');const part=toggleChild(null,all,'X',false);expect(part).toEqual(['Y',null]);expect(selectionState(part,all)).toBe('partial');expect(selectionState(toggleChild(part,all,'X',true),all)).toBe('all')});
it('same child under independent tags remains independent',()=>{const a=toggleChild(undefined,['X'],'X',true);const b=toggleChild(undefined,['X'],'X',false);expect(a).toEqual(['X']);expect(b).toEqual([])});
