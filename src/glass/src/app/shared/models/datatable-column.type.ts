import { PipeTransform, TemplateRef } from '@angular/core';

export type DatatableColumn = {
  cols?: number;
  css?: string;
  name: string;
  prop: string;
  compareProp?: string;
  cellTemplateName?: string;
  cellTemplateConfig?: any;
  cellTemplate?: TemplateRef<any>;
  pipe?: PipeTransform;
  unsortable?: boolean;
  align?: 'start' | 'center' | 'end';
};
