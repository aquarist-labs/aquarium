import { Directive, EventEmitter, OnDestroy, OnInit, Output } from '@angular/core';
import * as _ from 'lodash';
import { Observable, Subscription } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Directive()
// eslint-disable-next-line @angular-eslint/directive-class-suffix
export abstract class AbstractDashboardWidget<T> implements OnInit, OnDestroy {
  @Output()
  readonly loadDataEvent = new EventEmitter<T>();

  error = false;
  data?: T;

  protected refreshDataSubscription?: Subscription;

  get reloadPeriod(): number {
    return 5000;
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
    this.error = false;
    this.refreshDataSubscription = this.loadData()
      .pipe(
        // @ts-ignore
        catchError((err) => {
          if (_.isFunction(err.preventDefault)) {
            err.preventDefault();
          }
          this.error = true;
        })
      )
      .subscribe((data) => {
        this.refreshDataSubscription?.unsubscribe();
        this.data = data;
        this.loadDataEvent.emit(data);
        if (this.isAutoReloadable()) {
          setTimeout(() => {
            this.refreshData();
          }, this.reloadPeriod);
        }
      });
  }

  abstract loadData(): Observable<T>;
}
