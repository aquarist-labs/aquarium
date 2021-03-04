import { AfterViewInit, Component, Input, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { MatPaginator } from '@angular/material/paginator';
import { Sort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import * as _ from 'lodash';

import { DatatableColumn } from '~/app/shared/models/datatable-column.type';

export type DatatableData = Record<string, any>;

@Component({
  selector: 'glass-datatable',
  templateUrl: './datatable.component.html',
  styleUrls: ['./datatable.component.scss']
})
export class DatatableComponent implements OnInit, AfterViewInit {
  @ViewChild(MatPaginator)
  paginator?: MatPaginator;

  @ViewChild('iconTpl', { static: true })
  iconTpl?: TemplateRef<any>;
  @ViewChild('checkIconTpl', { static: true })
  checkIconTpl?: TemplateRef<any>;
  @ViewChild('yesNoIconTpl', { static: true })
  yesNoIconTpl?: TemplateRef<any>;

  @Input()
  get data(): DatatableData[] {
    return this.dataSource.data;
  }
  set data(data: DatatableData[]) {
    this.dataSource.data = data;
  }

  @Input()
  columns: DatatableColumn[] = [];

  // Set to 0 to disable pagination.
  @Input()
  pageSize = 25;

  @Input()
  hidePageSize = false;

  // Internal
  cellTemplates: Record<string, TemplateRef<any>> = {};
  displayedColumns: string[] = [];
  dataSource = new MatTableDataSource<DatatableData>([]);

  constructor() {}

  ngOnInit(): void {
    this.initTemplates();
    if (this.columns) {
      this.displayedColumns = _.map(this.columns, 'prop');
      _.forEach(this.columns, (column) => {
        if (_.isString(column.cellTemplateName)) {
          column.cellTemplate = this.cellTemplates[column.cellTemplateName];
        }
      });
    }
  }

  ngAfterViewInit() {
    if (this.paginator) {
      this.dataSource.paginator = this.paginator;
    }
  }

  initTemplates() {
    this.cellTemplates = {
      icon: this.iconTpl!,
      checkIcon: this.checkIconTpl!,
      yesNoIcon: this.yesNoIconTpl!
    };
  }

  renderCellValue(row: DatatableData, column: DatatableColumn): any {
    let value = _.get(row, column.prop);
    if (column.pipe && _.isFunction(column.pipe.transform)) {
      value = column.pipe.transform(value);
    }
    return value;
  }

  sortData(sort: Sort) {
    if (!sort.active || sort.direction === '') {
      return;
    }
    this.data = _.orderBy(this.data, [sort.active], [sort.direction]);
  }
}
