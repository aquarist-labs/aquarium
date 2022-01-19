/* eslint-disable no-underscore-dangle */
/*
 * Project Aquarium's frontend (glass)
 * Copyright (C) 2021 SUSE, LLC.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */
import {
  Component,
  EventEmitter,
  Input,
  NgZone,
  OnDestroy,
  OnInit,
  Output,
  TemplateRef,
  ViewChild
} from '@angular/core';
import * as _ from 'lodash';
import { Subscription, timer } from 'rxjs';

import { Icon } from '~/app/shared/enum/icon.enum';
import {
  DatatableCellTemplateName,
  DatatableColumn
} from '~/app/shared/models/datatable-column.type';
import { DatatableData } from '~/app/shared/models/datatable-data.type';

export enum SortDirection {
  ascending = 'asc',
  descending = 'desc'
}

@Component({
  selector: 'glass-datatable',
  templateUrl: './datatable.component.html',
  styleUrls: ['./datatable.component.scss']
})
export class DatatableComponent implements OnInit, OnDestroy {
  @ViewChild('iconTpl', { static: true })
  iconTpl?: TemplateRef<any>;
  @ViewChild('checkIconTpl', { static: true })
  checkIconTpl?: TemplateRef<any>;
  @ViewChild('yesNoIconTpl', { static: true })
  yesNoIconTpl?: TemplateRef<any>;
  @ViewChild('rowSelectTpl', { static: true })
  rowSelectTpl?: TemplateRef<any>;
  @ViewChild('actionMenuTpl', { static: true })
  actionMenuTpl?: TemplateRef<any>;
  @ViewChild('mapTpl', { static: true })
  mapTpl?: TemplateRef<any>;
  @ViewChild('badgeTpl', { static: true })
  badgeTpl?: TemplateRef<any>;

  @Input()
  columns: DatatableColumn[] = [];

  // Set to 0 to disable pagination.
  @Input()
  pageSize = 25;

  @Input()
  sortHeader?: string;

  @Input()
  sortDirection: SortDirection.ascending | SortDirection.descending = SortDirection.ascending;

  @Input()
  hidePageSize = false;

  // The auto-reload time in milliseconds. The load event will be fired
  // immediately. Set to `0` or `false` to disable this feature.
  // Defaults to `15000`.
  @Input()
  autoReload: number | boolean = 15000;

  // Row property used as unique identifier for the shown data. Only used if
  // the row selection is enabled. Will throw an error if property not found
  // in given columns. Defaults to 'id'.
  @Input()
  identifier = 'id';

  // Defines the following row selection types:
  // none: no row selection
  // single: allows single-select
  // multi: allows multi-select
  // Defaults to no row selection.
  @Input()
  selectionType: 'single' | 'multi' | 'none' = 'none';

  @Input()
  selected: Array<DatatableData> = [];

  @Output()
  loadData = new EventEmitter();

  @Output()
  selectionChange = new EventEmitter<DatatableData[]>();

  // Internal
  public icons = Icon;
  public page = 1;
  public cellTemplates: Record<string, TemplateRef<any>> = {};
  public displayedColumns: string[] = [];

  protected _data: Array<DatatableData> = [];
  protected subscriptions: Subscription = new Subscription();

  private sortableColumns: string[] = [];
  private tableData: DatatableData[] = [];

  constructor(private ngZone: NgZone) {}

  @Input()
  get data(): DatatableData[] {
    return this._data;
  }

  set data(data: DatatableData[]) {
    this._data = data;
  }

  // eslint-disable-next-line @typescript-eslint/member-ordering
  get filteredData(): DatatableData[] {
    const filtered = _.orderBy(this.data, [this.sortHeader], [this.sortDirection]).slice(
      (this.page - 1) * this.pageSize,
      (this.page - 1) * this.pageSize + this.pageSize
    );
    if (!_.isEqual(filtered, this.tableData)) {
      this.tableData = filtered;
    }
    return this.tableData;
  }

  ngOnInit(): void {
    this.initTemplates();
    if (this.columns) {
      // Sanitize the columns.
      _.forEach(this.columns, (column: DatatableColumn) => {
        _.defaultsDeep(column, {
          sortable: true
        });
        column.css = ['glass-text-no-overflow', column.css].join(' ').trim();
        if (_.isString(column.cellTemplateName)) {
          column.cellTemplate = this.cellTemplates[column.cellTemplateName];
          switch (column.cellTemplateName) {
            case 'actionMenu':
              column.name = '';
              column.prop = '_action'; // Add a none existing name here.
              column.sortable = false;
              column.cols = 1;
              column.css = '';
              break;
          }
        }
      });

      if (this.selectionType !== 'none') {
        if (!_.find(this.columns, ['prop', this.identifier])) {
          throw new Error(`Identifier "${this.identifier}" not found in defined columns.`);
        }
        this.columns.unshift({
          name: '',
          prop: '_rowSelect',
          cellTemplate: this.cellTemplates[DatatableCellTemplateName.rowSelect],
          cols: 1,
          sortable: false,
          align: 'center'
        });
      }
      // Get the columns to be displayed.
      this.displayedColumns = _.map(this.columns, 'prop');
    }
    if (_.isInteger(this.autoReload) && this.autoReload > 0) {
      this.ngZone.runOutsideAngular(() => {
        this.subscriptions.add(
          timer(0, this.autoReload as number).subscribe(() => {
            this.ngZone.run(() => this.reloadData());
          })
        );
      });
    }
    this.sortableColumns = this.columns
      .filter((c) => c.sortable === true)
      .map((c) => this.getSortProp(c));
    if (!this.sortHeader && this.sortableColumns.length > 0) {
      this.sortHeader = this.sortableColumns[0];
    }
    this.prepareColumnStyle();
  }

  ngOnDestroy() {
    this.subscriptions.unsubscribe();
  }

  initTemplates() {
    this.cellTemplates = {
      icon: this.iconTpl!,
      checkIcon: this.checkIconTpl!,
      yesNoIcon: this.yesNoIconTpl!,
      rowSelect: this.rowSelectTpl!,
      actionMenu: this.actionMenuTpl!,
      map: this.mapTpl!,
      badge: this.badgeTpl!
    };
  }

  renderCellValue(row: DatatableData, column: DatatableColumn): any {
    let value = _.get(row, column.prop);
    if (column.pipe && _.isFunction(column.pipe.transform)) {
      value = column.pipe.transform(value);
    }
    if (column.prop === '_rowSelect') {
      const item = _.find(this.selected, [this.identifier, row[this.identifier]]);
      if (item) {
        value = true;
      }
    }
    return value;
  }

  renderCellDisabled(row: DatatableData, column: DatatableColumn): any {
    if (column.prop === '_rowSelect') {
      if (this.selectionType === 'single') {
        const item = _.find(this.selected, [this.identifier, row[this.identifier]]);
        if (!item && this.selected.length > 0) {
          return true;
        }
      }
    }
    return false;
  }

  updateSorting(c: DatatableColumn): void {
    const prop = this.getSortProp(c);
    if (!this.sortableColumns.includes(prop)) {
      return;
    }
    if (prop === this.sortHeader) {
      this.sortDirection =
        this.sortDirection === SortDirection.descending
          ? SortDirection.ascending
          : SortDirection.descending;
    } else {
      this.sortHeader = prop;
      this.sortDirection = SortDirection.ascending;
    }
  }

  setHeaderClasses(column: DatatableColumn): string {
    let css = column.css || '';
    if (column.sortable !== true) {
      return css;
    }
    css += ' sortable';
    if (this.sortHeader !== this.getSortProp(column)) {
      return css;
    }
    return css + ` sort-header ${this.sortDirection}`;
  }

  getHeaderIconCss(): string {
    const css = 'mdi mdi-';
    return this.sortDirection === SortDirection.ascending
      ? css + 'sort-ascending'
      : css + 'sort-descending';
  }

  reloadData(): void {
    this.loadData.emit();
    this.updateSelection();
  }

  onPageSizeChange(pageSize: number): void {
    this.pageSize = pageSize;
    this.reloadData();
  }

  onSelectionChange($event: any, row: DatatableData) {
    if ($event.target.checked) {
      this.selected.push(row);
    } else {
      const selectedIndex = _.findIndex(this.selected, [this.identifier, row[this.identifier]]);
      if (selectedIndex >= 0) {
        this.selected.splice(selectedIndex, 1);
      }
    }
    this.selectionChange.emit(this.selected);
  }

  updateSelection(): void {
    const updatedSelection: Array<DatatableData> = [];
    this.selected.forEach((selectedItem) => {
      const item = _.find(this.data, [this.identifier, selectedItem[this.identifier]]);
      if (item) {
        updatedSelection.push(item);
      }
    });
    this.selected.splice(0, this.selected.length, ...updatedSelection);
  }

  private getSortProp(column: DatatableColumn): string {
    return column.compareProp || column.prop;
  }

  private prepareColumnStyle() {
    const customCols = this.columns.filter((c) => c.cols);
    const availableCols = 12 - _.sumBy(customCols, (c) => c.cols as number);
    const columnsToChange = this.columns.length - customCols.length;

    this.colSanityCheck(availableCols, columnsToChange);
    const autoColLength = columnsToChange === 0 ? 0 : Math.round(availableCols / columnsToChange);
    const flexFillIndex = this.findFlexFillIndex(customCols, columnsToChange);
    this.columns.forEach((column, index) => {
      if (!column.cols) {
        column.cols = autoColLength;
      }
      this.appendCss(column, index === flexFillIndex ? 'flex-fill' : `col-${column.cols}`);
    });
  }

  private colSanityCheck(availableCols: number, columnsToChange: number) {
    if (availableCols < 0 || (availableCols === 0 && columnsToChange >= 1)) {
      throw new Error(
        'Only 12 cols can be used in one row by Bootstrap, please redefine the "DatatableColumn.cols" values'
      );
    }
  }

  private findFlexFillIndex(customCols: DatatableColumn[], columnsToChange: number): number {
    return customCols.length === 0
      ? this.columns.length - 1
      : columnsToChange === 0
      ? _.findIndex(
          this.columns,
          customCols.reduce((p, c) => (p.cols! < c.cols! ? c : p))
        )
      : _.findLastIndex(this.columns, (c) => !c.cols);
  }

  private appendCss(column: DatatableColumn, css: string) {
    column.css = column.css ? `${column.css} ${css}` : css;
  }
}
