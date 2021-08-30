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
import { MatPaginator } from '@angular/material/paginator';
import { Sort } from '@angular/material/sort';
import * as _ from 'lodash';
import { Subscription, timer } from 'rxjs';

import { Icon } from '~/app/shared/enum/icon.enum';
import { DatatableColumn } from '~/app/shared/models/datatable-column.type';
import { DatatableData } from '~/app/shared/models/datatable-data.type';

@Component({
  selector: 'glass-datatable',
  templateUrl: './datatable.component.html',
  styleUrls: ['./datatable.component.scss']
})
export class DatatableComponent implements OnInit, OnDestroy {
  @ViewChild(MatPaginator)
  paginator?: MatPaginator;

  @ViewChild('iconTpl', { static: true })
  iconTpl?: TemplateRef<any>;
  @ViewChild('checkIconTpl', { static: true })
  checkIconTpl?: TemplateRef<any>;
  @ViewChild('yesNoIconTpl', { static: true })
  yesNoIconTpl?: TemplateRef<any>;
  @ViewChild('actionMenuTpl', { static: true })
  actionMenuTpl?: TemplateRef<any>;
  @ViewChild('mapTpl', { static: true })
  mapTpl?: TemplateRef<any>;

  @Input()
  get data(): DatatableData[] {
    return this._data;
  }
  set data(data: DatatableData[]) {
    this._data = data;
  }

  @Input()
  columns: DatatableColumn[] = [];

  // Set to 0 to disable pagination.
  @Input()
  pageSize = 25;

  @Input()
  hidePageSize = false;

  // The auto-reload time in milliseconds. The load event will be fired
  // immediately. Set to `0` or `false` to disable this feature.
  // Defaults to `15000`.
  @Input()
  autoReload: number | boolean = 15000;

  @Output()
  loadData = new EventEmitter();

  // Internal
  public icons = Icon;
  public page = 1;
  public cellTemplates: Record<string, TemplateRef<any>> = {};
  public displayedColumns: string[] = [];

  protected _data: Array<DatatableData> = [];
  protected subscriptions: Subscription = new Subscription();

  constructor(private ngZone: NgZone) {}

  ngOnInit(): void {
    this.initTemplates();
    if (this.columns) {
      // Sanitize the columns.
      _.forEach(this.columns, (column: DatatableColumn) => {
        if (_.isString(column.cellTemplateName)) {
          column.cellTemplate = this.cellTemplates[column.cellTemplateName];
          switch (column.cellTemplateName) {
            case 'actionMenu':
              column.name = '';
              column.prop = '_action'; // Add a none existing name here.
              column.sortable = false;
              break;
          }
        }
      });
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
  }

  ngOnDestroy() {
    this.subscriptions.unsubscribe();
  }

  initTemplates() {
    this.cellTemplates = {
      icon: this.iconTpl!,
      checkIcon: this.checkIconTpl!,
      yesNoIcon: this.yesNoIconTpl!,
      actionMenu: this.actionMenuTpl!,
      map: this.mapTpl!
    };
  }

  renderCellValue(row: DatatableData, column: DatatableColumn): any {
    let value = _.get(row, column.prop);
    if (column.pipe && _.isFunction(column.pipe.transform)) {
      value = column.pipe.transform(value);
    }
    return value;
  }

  sortData(sort: Sort): void {
    if (!sort.active || sort.direction === '') {
      return;
    }
    this.data = _.orderBy(this.data, [sort.active], [sort.direction]);
  }

  reloadData(): void {
    this.loadData.emit();
  }

  get filteredData(): DatatableData[] {
    return this.data.slice(
      (this.page - 1) * this.pageSize,
      (this.page - 1) * this.pageSize + this.pageSize
    );
  }
}
