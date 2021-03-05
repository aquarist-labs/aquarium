import { PipeTransform, TemplateRef } from '@angular/core';

export type DatatableColumn = {
  name: string;
  prop: string;
  cellTemplateName?: string;
  cellTemplateConfig?: any;
  cellTemplate?: TemplateRef<any>;
  pipe?: PipeTransform;
  sortable?: boolean;
  align?: 'start' | 'center' | 'end';
};
