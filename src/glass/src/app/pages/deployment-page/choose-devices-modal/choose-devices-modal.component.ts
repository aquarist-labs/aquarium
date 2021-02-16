import { Component, OnInit } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'glass-assimilate-devices-modal',
  templateUrl: './choose-devices-modal.component.html',
  styleUrls: ['./choose-devices-modal.component.scss']
})
export class ChooseDevicesModalComponent implements OnInit {
  constructor(public dialogRef: MatDialogRef<ChooseDevicesModalComponent>) {}

  ngOnInit(): void {}
}
