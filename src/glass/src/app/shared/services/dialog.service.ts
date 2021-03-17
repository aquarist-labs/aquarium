import { ComponentType } from '@angular/cdk/portal';
import { Injectable } from '@angular/core';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';

import { CephfsModalComponent } from '~/app/pages/deployment-page/cephfs-modal/cephfs-modal.component';

@Injectable({
  providedIn: 'root'
})
export class DialogService {
  private defaultDialogSettings = { width: '60%' };

  constructor(private dialog: MatDialog) {}

  openCephfs(onClose: (result: boolean) => void): void {
    this.open(CephfsModalComponent, onClose);
  }

  open(
    component: ComponentType<any>,
    onClose: (result: boolean) => void,
    config: MatDialogConfig = this.defaultDialogSettings
  ) {
    const ref = this.dialog.open(component, config);
    ref.afterClosed().subscribe({ next: onClose });
  }
}
