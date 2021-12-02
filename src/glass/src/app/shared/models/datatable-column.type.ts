import { PipeTransform, TemplateRef } from '@angular/core';

export enum DatatableCellTemplateName {
  icon = 'icon',
  checkIcon = 'checkIcon',
  yesNoIcon = 'yesNoIcon',
  rowSelect = 'rowSelect',
  // Display a drop-down menu.
  // {
  //   ...
  //   cellTemplateName: DatatableCellTemplateName.actionMenu,
  //   cellTemplateConfig: (rowData: Record<string, any>) => DatatableActionItem[]
  // }
  actionMenu = 'actionMenu',
  // Map the cell value to something different.
  // {
  //   ...
  //   cellTemplateName: DatatableCellTemplateName.map,
  //   cellTemplateConfig: {
  //     [key: any]: any
  //   }
  // }
  map = 'map',
  // Display the cell value as badge(s).
  // {
  //   ...
  //   cellTemplateName: DatatableCellTemplateName.badge,
  //   cellTemplateConfig: {
  //     class?: string; // Additional class name.
  //     prefix?: any;   // Prefix of the value to be displayed.
  //                     // 'map' and 'prefix' exclude each other.
  //     map?: {
  //       [key: any]: { value: any, class?: string }
  //     }
  //   }
  // }
  badge = 'badge'
}

export type DatatableColumn = {
  cols?: number;
  css?: string;
  name: string;
  prop: string;
  compareProp?: string;
  cellTemplateName?: DatatableCellTemplateName;
  cellTemplateConfig?: any;
  cellTemplate?: TemplateRef<any>;
  pipe?: PipeTransform;
  sortable?: boolean; // Defaults to 'true'.
  align?: 'start' | 'center' | 'end';
};
