import { Component, Input } from '@angular/core';
import { MatSidenav } from '@angular/material/sidenav';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';

import { DialogComponent } from '~/app/shared/components/dialog/dialog.component';
import { AuthService } from '~/app/shared/services/api/auth.service';
import { AuthStorageService } from '~/app/shared/services/auth-storage.service';
import { DialogService } from '~/app/shared/services/dialog.service';

@Component({
  selector: 'glass-top-bar',
  templateUrl: './top-bar.component.html',
  styleUrls: ['./top-bar.component.scss']
})
export class TopBarComponent {
  // eslint-disable-next-line @angular-eslint/no-input-rename
  @Input('navigationSidenav')
  navigationSidenav!: MatSidenav;

  username: string | null;

  constructor(
    private authService: AuthService,
    private authStorageService: AuthStorageService,
    private dialogService: DialogService
  ) {
    this.username = this.authStorageService.getUsername();
  }

  onToggleNavigationBar(): void {
    this.navigationSidenav.toggle();
  }

  onLogout(): void {
    this.dialogService.open(
      DialogComponent,
      (res: boolean) => {
        if (res) {
          this.authService.logout().subscribe();
        }
      },
      {
        width: '40%',
        data: {
          type: 'yesNo',
          icon: 'question',
          message: TEXT('Do you really want to logout?')
        }
      }
    );
  }
}
