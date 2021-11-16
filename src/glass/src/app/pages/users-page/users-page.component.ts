/*
 * Project Aquarium's frontend (glass)
 * Copyright (C) 2021 SUSE, LLC.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */
import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { BlockUI, NgBlockUI } from 'ng-block-ui';
import { finalize } from 'rxjs/operators';

import { translate } from '~/app/i18n.helper';
import { PageStatus } from '~/app/shared/components/content-page/content-page.component';
import { DialogComponent } from '~/app/shared/components/dialog/dialog.component';
import { DatatableActionItem } from '~/app/shared/models/datatable-action-item.type';
import {
  DatatableCellTemplateName,
  DatatableColumn
} from '~/app/shared/models/datatable-column.type';
import { User, UsersService } from '~/app/shared/services/api/users.service';
import { DialogService } from '~/app/shared/services/dialog.service';
@Component({
  selector: 'glass-users-page',
  templateUrl: './users-page.component.html',
  styleUrls: ['./users-page.component.scss']
})
export class UsersPageComponent {
  @BlockUI()
  blockUI!: NgBlockUI;

  pageStatus: PageStatus = PageStatus.none;
  data: User[] = [];
  columns: DatatableColumn[];

  private firstLoadComplete = false;

  constructor(
    private dialogService: DialogService,
    private usersService: UsersService,
    private router: Router
  ) {
    this.columns = [
      {
        name: TEXT('Name'),
        prop: 'username'
      },
      {
        name: TEXT('Full Name'),
        prop: 'full_name'
      },
      {
        name: TEXT('Disabled'),
        prop: 'disabled',
        cellTemplateName: DatatableCellTemplateName.checkIcon
      },
      {
        name: '',
        prop: '',
        cellTemplateName: DatatableCellTemplateName.actionMenu,
        cellTemplateConfig: this.getActionMenu.bind(this)
      }
    ];
  }

  loadData(): void {
    if (!this.firstLoadComplete) {
      this.pageStatus = PageStatus.loading;
    }
    this.usersService
      .list()
      .pipe(
        finalize(() => {
          this.firstLoadComplete = true;
        })
      )
      .subscribe(
        (data: User[]) => {
          this.data = data;
          this.pageStatus = PageStatus.ready;
        },
        () => (this.pageStatus = PageStatus.loadingError)
      );
  }

  private getActionMenu(user: User): DatatableActionItem[] {
    return [
      {
        title: TEXT('Edit'),
        callback: () => this.router.navigate([`dashboard/users/edit/${user.username}`])
      },
      {
        type: 'divider'
      },
      {
        title: TEXT('Delete'),
        callback: () => this.openDeletionDialog(user.username)
      }
    ];
  }

  private openDeletionDialog(username: string) {
    this.dialogService.open(
      DialogComponent,
      (res: boolean) => {
        if (res) {
          this.blockUI.start(translate(TEXT('Please wait, deleting user ...')));
          this.usersService
            .delete(username)
            .pipe(finalize(() => this.blockUI.stop()))
            .subscribe(() => {
              this.loadData();
            });
        }
      },
      {
        type: 'yesNo',
        icon: 'question',
        message: TEXT(`Do you really want to delete user <strong>${username}</strong>?`)
      }
    );
  }
}
