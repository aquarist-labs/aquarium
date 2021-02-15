import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'glass-deployment-page',
  templateUrl: './deployment-page.component.html',
  styleUrls: ['./deployment-page.component.scss']
})
export class DeploymentPageComponent implements OnInit {
  nfs = false;

  constructor() {}

  ngOnInit(): void {}

  addNfs(): void {
    this.nfs = true;
  }
}
