// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
import { Component, Injector, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, convertToParamMap, ParamMap } from '@angular/router';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { switchMap, tap } from 'rxjs/operators';

import { ChannelService, keyChannelStrim } from '@app/core/services';
import { ClusterService, WorkerInstance } from '@app/core/services/cluster.service';
import { EventMessage, getNavigationPath, setPathOfRoute, SocketState } from '@app/core/store';
import { Cluster, EmmitRow, Host, IAction, isIssue, Issue, Job } from '@app/core/types';
import { SocketListenerDirective } from '@app/shared/directives/socketListener.directive';
import { IDetails } from './navigation.service';
import { AdcmEntity } from '@app/models/entity';
import { EntityService } from '@app/abstract/entity-service';

@Component({
  selector: 'app-detail',
  templateUrl: './detail.component.html',
  styleUrls: ['./detail.component.scss'],
})
export class DetailComponent extends SocketListenerDirective implements OnInit, OnDestroy {
  request$: Observable<WorkerInstance>;
  upgradable = false;
  actions: IAction[] = [];
  status: number | string;
  issue: Issue;
  current: IDetails;
  currentName = '';

  navigationPath: Observable<AdcmEntity[]> = this.store.select(getNavigationPath).pipe(this.takeUntil());

  entityService: EntityService<any>;

  constructor(
    socket: Store<SocketState>,
    private route: ActivatedRoute,
    private service: ClusterService,
    private channel: ChannelService,
    private store: Store,
    injector: Injector
  ) {
    super(socket);
    const serviceToken = route.snapshot.data['entityService'];
    if (serviceToken) {
      this.entityService = injector.get<EntityService<any>>(serviceToken);
    }
  }

  get Current() {
    return this.service.Current;
  }

  ngOnInit(): void {
    this.request$ = this.route.paramMap.pipe(
      tap((data) => console.log('this.request$ = : ', data)),
      switchMap((param) => this.service.getContext(param, this.entityService)),
      tap((w) => this.run(w))
    );

    super.startListenSocket();
  }

  ngOnDestroy(): void {
    this.service.clearWorker();
  }

  get isIssue() {
    return isIssue(this.issue);
  }

  run(w: WorkerInstance) {
    const {
      id,
      name,
      typeName,
      action,
      actions,
      issue,
      status,
      prototype_name,
      prototype_display_name,
      prototype_version,
      bundle_id,
      state,
    } = w.current;
    const { upgradable, upgrade, hostcomponent } = w.current as Cluster;
    const { log_files, objects } = w.current as Job;
    const { provider_id } = w.current as Host;

    this.currentName = name;
    this.actions = actions;
    this.upgradable = upgradable;
    this.status = status;

    const parent = w.current.typeName === 'cluster' ? null : w.cluster;
    this.issue = issue;

    this.current = {
      parent,
      id,
      name,
      typeName,
      actions,
      action,
      issue,
      upgradable,
      upgrade,
      status,
      state,
      log_files,
      objects,
      prototype_name,
      prototype_display_name,
      prototype_version,
      provider_id,
      bundle_id,
      hostcomponent,
    };
  }

  scroll(stop: { direct: -1 | 1 | 0; screenTop: number }) {
    this.channel.next(keyChannelStrim.scroll, stop);
  }

  reset() {
    this.request$ = this.service.reset().pipe(
      this.takeUntil(),
      tap((a) => this.run(a))
    );
  }

  socketListener(m: EventMessage) {
    if ((m.event === 'create' || m.event === 'delete') && m.object.type === 'bundle') {
      this.reset();
      return;
    }

    const type = m.object.type === 'component' ? 'servicecomponent' : m.object.type;
    if (this.Current?.typeName === type && this.Current?.id === m.object.id) {
      if (this.service.Current.typeName === 'job' && (m.event === 'change_job_status' || m.event === 'add_job_log')) {
        this.reset();
        return;
      }

      if (m.event === 'change_state' || m.event === 'upgrade') {
        this.reset();
        return;
      }
      if (m.event === 'clear_issue') {
        this.issue = {};
        this.Current.issue = this.issue;
      }
      if (m.event === 'raise_issue') this.issue = m.object.details.value;
      if (m.event === 'change_status') this.status = +m.object.details.value;
    }

    // parent
    if (this.service.Cluster?.id === m.object.id && this.Current?.typeName !== 'cluster' && type === 'cluster' && m.event === 'clear_issue') this.issue = {};
  }

  refresh(event: EmmitRow): void {
    const { row } = event;

    const params: ParamMap = convertToParamMap({ cluster: row.id });
    this.store.dispatch(setPathOfRoute({ params }));

  }
}
