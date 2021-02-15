import { Component } from '@angular/core';
import * as _ from 'lodash';
import { Observable, of, Subscription } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { AbstractDashboardWidget } from '~/app/core/dashboard/widgets/abstract-dashboard-widget';

@Component({
  selector: 'glass-health-dashboard-widget',
  templateUrl: './health-dashboard-widget.component.html',
  styleUrls: ['./health-dashboard-widget.component.scss']
})
export class HealthDashboardWidgetComponent extends AbstractDashboardWidget<boolean> {
  data = false;
  error = false;

  protected subscription: Subscription = new Subscription();

  constructor() {
    super();
    this.subscription = this.loadDataEvent.subscribe(() => {
      this.error = false;
    });
  }

  loadData(): Observable<boolean> {
    return of(!this.data).pipe(
      // @ts-ignore
      catchError((err) => {
        if (_.isFunction(err.preventDefault)) {
          err.preventDefault();
        }
        this.error = true;
      })
    );
  }
}
