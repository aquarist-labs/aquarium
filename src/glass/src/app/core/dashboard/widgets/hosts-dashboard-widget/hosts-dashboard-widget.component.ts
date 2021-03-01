import { Component } from '@angular/core';
import { Observable } from 'rxjs';

import { AbstractDashboardWidget } from '~/app/core/dashboard/widgets/abstract-dashboard-widget';
import { Host, OrchService } from '~/app/shared/services/api/orch.service';

@Component({
  selector: 'glass-hosts-dashboard-widget',
  templateUrl: './hosts-dashboard-widget.component.html',
  styleUrls: ['./hosts-dashboard-widget.component.scss']
})
export class HostsDashboardWidgetComponent extends AbstractDashboardWidget<Host[]> {
  data: Host[] = [];
  displayedColumns: string[] = ['hostname', 'address'];

  constructor(private orchService: OrchService) {
    super();
  }

  loadData(): Observable<Host[]> {
    return this.orchService.hosts();
  }
}
