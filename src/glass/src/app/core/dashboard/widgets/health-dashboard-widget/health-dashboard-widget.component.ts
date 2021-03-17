import { Component } from '@angular/core';
import { Observable } from 'rxjs';

import { Status, StatusService } from '~/app/shared/services/api/status.service';

@Component({
  selector: 'glass-health-dashboard-widget',
  templateUrl: './health-dashboard-widget.component.html',
  styleUrls: ['./health-dashboard-widget.component.scss']
})
export class HealthDashboardWidgetComponent {
  public isError = false;
  public isWarn = false;
  public isOkay = false;
  public hasStatus = false;

  public constructor(private statusService: StatusService) {}

  setHealthStatus(status: Status) {
    this.isError = this.isWarn = this.isOkay = false;
    this.hasStatus = false;

    if (!status.cluster) {
      return;
    }

    this.hasStatus = true;
    switch (status.cluster.health.status.toLowerCase()) {
      case 'health_ok':
        this.isOkay = true;
        break;
      case 'health_warn':
        this.isWarn = true;
        break;
      case 'health_err':
        this.isError = true;
        break;
      default:
        this.hasStatus = false;
        break;
    }
  }

  loadData(): Observable<Status> {
    return this.statusService.status();
  }
}
