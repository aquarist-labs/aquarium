import { Directive, EventEmitter, OnDestroy, OnInit, Output } from '@angular/core';
import * as _ from 'lodash';
import { EMPTY, Observable, Subscription } from 'rxjs';
import { catchError, finalize } from 'rxjs/operators';

@Directive()
// eslint-disable-next-line @angular-eslint/directive-class-suffix
export abstract class AbstractDashboardWidget<T> implements OnInit, OnDestroy {
  @Output()
  readonly loadDataEvent = new EventEmitter<T>();

  error = false;
  firstLoadComplete = false;
  loading = false;
  data?: T;

  protected refreshDataSubscription?: Subscription;

  get reloadPeriod(): number {
    return 15000;
  }

  ngOnInit(): void {
    this.refreshData();
  }

  ngOnDestroy(): void {
    this.refreshDataSubscription?.unsubscribe();
  }

  protected isAutoReloadable(): boolean {
    return this.reloadPeriod > 0;
  }

  protected refreshData(): void {
    this.loading = true;
    this.refreshDataSubscription = this.loadData()
      .pipe(
        // @ts-ignore
        catchError((err) => {
          if (_.isFunction(err.preventDefault)) {
            err.preventDefault();
          }
          this.error = true;
          return EMPTY;
        }),
        finalize(() => {
          if (!this.error && !this.firstLoadComplete) {
            this.firstLoadComplete = true;
          }
          this.loading = false;
          this.refreshDataSubscription?.unsubscribe();
          if (this.isAutoReloadable()) {
            setTimeout(() => {
              this.refreshData();
            }, this.reloadPeriod);
          }
        })
      )
      .subscribe((data) => {
        this.error = false;
        this.data = data;
        this.loadDataEvent.emit(data);
      });
  }

  abstract loadData(): Observable<T>;
}
