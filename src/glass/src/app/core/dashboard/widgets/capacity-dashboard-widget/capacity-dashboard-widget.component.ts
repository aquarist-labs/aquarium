import { Component } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import { translate } from '~/app/i18n.helper';
import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import { ServicesService, ServiceStorage } from '~/app/shared/services/api/services.service';

@Component({
  selector: 'glass-capacity-dashboard-widget',
  templateUrl: './capacity-dashboard-widget.component.html',
  styleUrls: ['./capacity-dashboard-widget.component.scss']
})
export class CapacityDashboardWidgetComponent {
  // Options for chart
  chartData: any[] = [];
  colorScheme = {
    // EOS colors: [$eos-bc-green-500, $eos-bc-gray-100]
    domain: ['#30ba78', '#e0dfdf']
  };

  constructor(private servicesService: ServicesService) {}

  updateChartData(data: Array<ServiceStorage>) {
    const used = _.sum(_.map(data, (serviceStorage: ServiceStorage) => serviceStorage.used));
    const avail = _.sum(_.map(data, (serviceStorage: ServiceStorage) => serviceStorage.avail));
    this.chartData = [
      { name: translate(TEXT('Used')), value: used },
      { name: translate(TEXT('Free')), value: avail }
    ];
  }

  valueFormatting(c: any) {
    // Note, this implementation is by intention, do NOT use code like
    // 'valueFormatting.bind(this)', otherwise this method is called
    // over and over again because Angular CD seems to assume something
    // has been changed.
    const pipe = new BytesToSizePipe();
    return pipe.transform(c);
  }

  loadData(): Observable<Array<ServiceStorage>> {
    return this.servicesService
      .stats()
      .pipe(map((data: Record<string, ServiceStorage>) => _.values(data)));
  }
}
