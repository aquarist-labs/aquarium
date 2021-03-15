import { Component } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { Observable } from 'rxjs';

import { translate } from '~/app/i18n.helper';
import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import { Reservations, ServicesService } from '~/app/shared/services/api/services.service';

@Component({
  selector: 'glass-capacity-dashboard-widget',
  templateUrl: './capacity-dashboard-widget.component.html',
  styleUrls: ['./capacity-dashboard-widget.component.scss']
})
export class CapacityDashboardWidgetComponent {
  // Options for chart
  chartData: any[] = [];
  colorScheme = {
    // EOS colors: [$eos-bc-green-500, $eos-bc-red-500]
    domain: ['#30ba78', '#dc3545']
  };

  constructor(public service: ServicesService, private bytesToSizePipe: BytesToSizePipe) {}

  updateChartData($data: Reservations) {
    this.chartData = [
      { name: translate(TEXT('Assigned')), value: $data.reserved },
      { name: translate(TEXT('Unassigned')), value: $data.available }
    ];
  }

  valueFormatting(c: any) {
    return this.bytesToSizePipe.transform(c);
  }

  loadData(): Observable<Reservations> {
    return this.service.reservations();
  }
}
