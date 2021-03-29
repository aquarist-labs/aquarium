import { Component } from '@angular/core';
import * as _ from 'lodash';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import { ServicesService, ServiceStorage } from '~/app/shared/services/api/services.service';

@Component({
  selector: 'glass-services-capacity-dashboard-widget',
  templateUrl: './services-capacity-dashboard-widget.component.html',
  styleUrls: ['./services-capacity-dashboard-widget.component.scss']
})
export class ServicesCapacityDashboardWidgetComponent {
  chartData: any[] = [];
  colorScheme = {
    domain: ['#00739c', '#fa9334', '#b54236', '#1c445c', '#00aab4']
  };

  constructor(private servicesService: ServicesService) {}

  loadData(): Observable<Array<ServiceStorage>> {
    return this.servicesService.stats().pipe(
      map((data: Record<string, ServiceStorage>): ServiceStorage[] => {
        const result: ServiceStorage[] = [];
        _.forEach(data, (serviceStorage: ServiceStorage) => {
          result.push(serviceStorage);
        });
        _.orderBy(result, ['utilization'], ['desc']);
        return _.take(result, 5);
      })
    );
  }

  updateChartData($data: ServiceStorage[]) {
    this.chartData = [];
    _.forEach($data, (serviceStorage: ServiceStorage) => {
      this.chartData.push({
        name: serviceStorage.name,
        value: serviceStorage.utilization
      });
    });
  }

  dataLabelFormatting(label: number): string {
    return `${(label * 100).toFixed(2)}%`;
  }
}
