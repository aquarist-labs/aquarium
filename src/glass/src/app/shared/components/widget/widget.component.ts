import { Component, EventEmitter, Input, OnDestroy, OnInit, Output } from '@angular/core';
import * as _ from 'lodash';
import { EMPTY, Observable, Subscription } from 'rxjs';
import { catchError, finalize } from 'rxjs/operators';

export type WidgetAction = {
  icon: string;
  name: string;
  action: () => void;
};

@Component({
  selector: 'glass-widget',
  templateUrl: './widget.component.html',
  styleUrls: ['./widget.component.scss']
})
export class WidgetComponent implements OnInit, OnDestroy {
  @Output()
  readonly loadDataEvent = new EventEmitter<any>();

  @Input()
  title = '';
  @Input()
  loadData?: () => Observable<any>;
  @Input()
  actionMenu?: WidgetAction[];

  error = false;
  loading = false;
  firstLoadComplete = false;
  data?: any;

  private loadingWithoutError = true;
  private refreshDataSubscription?: Subscription;

  private readonly reloadTime = 15000;

  ngOnInit(): void {
    this.reload();
  }

  ngOnDestroy(): void {
    this.refreshDataSubscription?.unsubscribe();
  }

  reload(): void {
    if (!this.loadData) {
      throw new Error('loadData attribute not set');
    }
    this.loading = true;
    this.loadingWithoutError = true;
    this.refreshDataSubscription = this.loadData()
      .pipe(
        // @ts-ignore
        catchError((err) => {
          if (_.isFunction(err.preventDefault)) {
            err.preventDefault();
          }
          this.loadingWithoutError = false;
          return EMPTY;
        }),
        finalize(() => {
          this.error = !this.loadingWithoutError;
          this.firstLoadComplete = this.loadingWithoutError;
          this.refreshDataSubscription?.unsubscribe();
          if (this.reloadTime > 0) {
            setTimeout(() => {
              this.reload();
            }, this.reloadTime);
          }
          this.loading = false;
        })
      )
      .subscribe((data) => {
        this.data = data;
        this.loadDataEvent.emit(data);
      });
  }
}
