import {
  AfterViewInit,
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
import { MatTableDataSource } from '@angular/material/table';
import * as _ from 'lodash';
import { Subscription, timer } from 'rxjs';

import { DatatableColumn } from '~/app/shared/models/datatable-column.type';
import { DatatableData } from '~/app/shared/models/datatable-data.type';

@Component({
  selector: 'glass-datatable',
  templateUrl: './datatable.component.html',
  styleUrls: ['./datatable.component.scss']
})
export class DatatableComponent implements OnInit, AfterViewInit, OnDestroy {
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

  // The auto-reload time in milliseconds. The load event will be fired
  // immediately. Set to `0` or `false` to disable this feature.
  // Defaults to `15000`.
  @Input()
  autoReload: number | boolean = 15000;

  @Output()
  loadData = new EventEmitter();

  // Internal
  cellTemplates: Record<string, TemplateRef<any>> = {};
  displayedColumns: string[] = [];
  dataSource = new MatTableDataSource<DatatableData>([]);

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

  ngAfterViewInit() {
    if (this.paginator) {
      this.dataSource.paginator = this.paginator;
    }
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
}
