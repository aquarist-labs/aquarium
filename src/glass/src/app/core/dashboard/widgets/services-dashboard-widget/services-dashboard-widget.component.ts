import { Component } from '@angular/core';
import { Observable } from 'rxjs';

import { AbstractDashboardWidget } from '~/app/core/dashboard/widgets/abstract-dashboard-widget';
import { ServiceDesc, ServicesService } from '~/app/shared/services/api/services.service';

@Component({
  selector: 'glass-services-dashboard-widget',
  templateUrl: './services-dashboard-widget.component.html',
  styleUrls: ['./services-dashboard-widget.component.scss']
})
export class ServicesDashboardWidgetComponent extends AbstractDashboardWidget<ServiceDesc[]> {
  data: ServiceDesc[] = [];
  displayedColumns: string[] = ['name', 'type'];

  constructor(private service: ServicesService) {
    super();
  }

  loadData(): Observable<ServiceDesc[]> {
    return this.service.list();
  }
}
