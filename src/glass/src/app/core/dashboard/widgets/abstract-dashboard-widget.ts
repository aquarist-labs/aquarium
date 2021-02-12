import { Directive, EventEmitter, OnDestroy, OnInit, Output } from '@angular/core';
import { Observable, Subscription } from 'rxjs';

@Directive()
// eslint-disable-next-line @angular-eslint/directive-class-suffix
export abstract class AbstractDashboardWidget<T> implements OnInit, OnDestroy {
  @Output()
  readonly loadDataEvent = new EventEmitter<T>();

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
    this.refreshDataSubscription = this.loadData().subscribe((data) => {
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
