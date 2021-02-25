import { Component, OnDestroy, OnInit } from '@angular/core';
import { Observable, Subscription } from 'rxjs';

import { AbstractDashboardWidget } from '~/app/core/dashboard/widgets/abstract-dashboard-widget';
import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import { Reservations, ServicesService } from '~/app/shared/services/api/services.service';

@Component({
  selector: 'glass-capacity-dashboard-widget',
  templateUrl: './capacity-dashboard-widget.component.html',
  styleUrls: ['./capacity-dashboard-widget.component.scss']
})
export class CapacityDashboardWidgetComponent
  extends AbstractDashboardWidget<Reservations>
  implements OnInit, OnDestroy {
  data: Reservations = { reserved: 0, available: 0 };

  // Options for chart
  // @ts-ignore
  chartData: any[];
  colorScheme = {
    // See default.scss -> [$eos-bc-green-500, $eos-bc-red-500]
    domain: ['#30ba78', '#dc3545']
  };

  protected subscription: Subscription = new Subscription();

  constructor(private service: ServicesService, private bytesToSizePipe: BytesToSizePipe) {
    super();
    // @ts-ignore
    this.subscription = this.loadDataEvent.subscribe(() => {
      this.chartData = [
        { name: 'Assigned', value: this.data.available - this.data.reserved },
        { name: 'Unassigned', value: this.data.reserved }
      ];
    });
  }

  ngOnInit(): void {
    super.ngOnInit();
  }

  valueFormatting(c: any) {
    return this.bytesToSizePipe.transform(c);
  }

  ngOnDestroy(): void {
    super.ngOnDestroy();
    this.subscription.unsubscribe();
  }

  loadData(): Observable<Reservations> {
    return this.service.reservations();
  }
}
