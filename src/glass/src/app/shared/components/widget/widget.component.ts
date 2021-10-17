import { Component, EventEmitter, Input, OnDestroy, OnInit, Output } from '@angular/core';
import * as _ from 'lodash';
import { EMPTY, Observable, Subscription, timer } from 'rxjs';
import { catchError, finalize, take, tap } from 'rxjs/operators';

import { LocalStorageService } from '~/app/shared/services/local-storage.service';

export type WidgetAction = {
  icon: string;
  name: string;
  action: () => void;
};

export enum WidgetHealthStatus {
  info = 'info',
  success = 'success',
  warning = 'warning',
  error = 'error',
  unknown = 'unknown'
}

@Component({
  selector: 'glass-widget',
  templateUrl: './widget.component.html',
  styleUrls: ['./widget.component.scss']
})
export class WidgetComponent implements OnInit, OnDestroy {
  @Input()
  widgetTitle = '';
  @Input()
  loadData?: () => Observable<any>;
  @Input()
  actionMenu?: WidgetAction[];
  @Input()
  setStatus?: (data: any) => WidgetHealthStatus;
  @Input()
  reloadTime = 15000;
  @Output()
  readonly loadDataEvent = new EventEmitter<any>();

  status: WidgetHealthStatus = WidgetHealthStatus.info;
  error = false;
  loading = false;
  firstLoadComplete = false;
  data?: any;
  isCollapsed = false;

  private loadDataSubscription?: Subscription;
  private timerSubscription?: Subscription;

  constructor(private localStorageService: LocalStorageService) {}

  ngOnInit(): void {
    this.isCollapsed = 'false' !== this.localStorageService.get(this.getKey(), 'false');
    this.reload();
  }

  ngOnDestroy(): void {
    this.loadDataSubscription?.unsubscribe();
    this.timerSubscription?.unsubscribe();
  }

  reload(): void {
    if (!this.loadData) {
      throw new Error('loadData attribute not set');
    }
    this.loading = true;
    this.loadDataSubscription = this.loadData()
      .pipe(
        // @ts-ignore
        catchError((err) => {
          if (_.isFunction(err.preventDefault)) {
            err.preventDefault();
          }
          this.loading = false;
          this.status = WidgetHealthStatus.unknown;
          this.error = true;
          return EMPTY;
        }),
        tap(() => {
          this.loading = false;
          this.error = false;
          this.firstLoadComplete = true;
        }),
        finalize(() => {
          if (this.reloadTime > 0) {
            this.timerSubscription = timer(this.reloadTime)
              .pipe(take(1))
              .subscribe(() => {
                this.loadDataSubscription!.unsubscribe();
                this.reload();
              });
          }
        })
      )
      .subscribe((data) => {
        this.data = data;
        this.status = this.setStatus ? this.setStatus(this.data) : WidgetHealthStatus.info;
        this.loadDataEvent.emit(data);
      });
  }

  toggleCollapsed(): void {
    this.isCollapsed = !this.isCollapsed;
    this.localStorageService.set(this.getKey(), String(this.isCollapsed));
  }

  private getKey(): string {
    return `glass_widget_${this.widgetTitle}_collapsed`;
  }
}
