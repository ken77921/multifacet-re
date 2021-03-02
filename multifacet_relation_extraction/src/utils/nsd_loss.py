import torch
import random
from model.model import MatrixReconstruction as MR

def predict_basis(model_set, n_basis, output_emb, predict_coeff_sum = False):

    if predict_coeff_sum:
        basis_pred, coeff_pred = model_set(output_emb, predict_coeff_sum = True)
        return basis_pred, coeff_pred
    else:
        basis_pred = model_set(output_emb, predict_coeff_sum = False)
        return basis_pred

def estimate_coeff_mat_batch_max_iter(target_embeddings, basis_pred, device):
    batch_size = target_embeddings.size(0)
    C = target_embeddings.permute(0,2,1)
    
    basis_pred_norm = basis_pred.norm(dim = 2, keepdim=True)
    XX = basis_pred_norm * basis_pred_norm
    n_not_sparse = 2
    coeff_mat_trans = torch.zeros(batch_size, basis_pred.size(1), target_embeddings.size(1), requires_grad= False, device=device )
    for i in range(n_not_sparse):
        XY = torch.bmm(basis_pred, C)
        coeff = XY / XX
        #coeff should have dimension ( n_batch, n_basis, n_set)
        max_v, max_i = torch.max(coeff, dim = 1, keepdim=True)
        max_v[max_v<0] = 0
    
        coeff_mat_trans_temp = torch.zeros(batch_size, basis_pred.size(1), target_embeddings.size(1), requires_grad= False, device=device )
        coeff_mat_trans_temp.scatter_(dim=1, index = max_i, src = max_v)
        coeff_mat_trans.scatter_add_(dim=1, index = max_i, src = max_v)
        #pred_emb = torch.bmm(coeff_mat_trans_temp.permute(0,2,1),basis_pred)
        pred_emb = torch.bmm(coeff_mat_trans.permute(0,2,1),basis_pred)
        C = (target_embeddings - pred_emb).permute(0,2,1)
    
    return coeff_mat_trans.permute(0,2,1)

def estimate_coeff_mat_batch_max_cos(target_embeddings, basis_pred):
    C = target_embeddings.permute(0,2,1)

    basis_pred_norm = basis_pred.norm(dim = 2, keepdim=True)
    XX = basis_pred_norm * basis_pred_norm
    XY = torch.bmm(basis_pred, C)
    coeff = XY / XX
    #coeff should have dimension ( n_batch, n_basis, n_set)
    max_v, max_i = torch.max(coeff, dim = 1)
    return max_v, max_i


def estimate_coeff_mat_batch_max(target_embeddings, basis_pred, device):
    batch_size = target_embeddings.size(0)
    C = target_embeddings.permute(0, 2, 1)

    basis_pred_norm = basis_pred.norm(dim=2, keepdim=True)
    XX = basis_pred_norm * basis_pred_norm
    XY = torch.bmm(basis_pred, C)
    XX = XX.expand(XY.shape)
    coeff = torch.where(XX == 0, XX, XY / XX)
    basis_pred_norm = basis_pred_norm.expand(XY.shape)
    cos_sim = torch.where(basis_pred_norm == 0, basis_pred_norm, XY / basis_pred_norm)
    # coeff should have dimension ( n_batch, n_basis, n_set)

    max_v_cos, max_i_cos = torch.max(cos_sim, dim=1, keepdim=True)
    max_v = torch.gather(coeff, dim=1, index=max_i_cos)
    max_v[max_v < 0] = 0
    max_v[max_v > 1] = 1

    coeff_mat_trans = torch.zeros(batch_size, basis_pred.size(1), target_embeddings.size(1), requires_grad=False,
                                  device=device)
    coeff_mat_trans.scatter_(dim=1, index=max_i_cos, src=max_v)
    return coeff_mat_trans.permute(0, 2, 1)

def estimate_coeff_mat_batch_opt(target_embeddings, basis_pred, L1_losss_B, device, coeff_opt, lr, max_iter):
    batch_size = target_embeddings.size(0)
    mr = MR(batch_size, target_embeddings.size(1), basis_pred.size(1), device=device)
    loss_func = torch.nn.MSELoss(reduction='sum')
    
    if coeff_opt == 'sgd':
        opt = torch.optim.SGD(mr.parameters(), lr=lr, momentum=0, dampening=0, weight_decay=0, nesterov=False)
    elif coeff_opt == 'asgd':
        opt = torch.optim.ASGD(mr.parameters(), lr=lr, lambd=0.0001, alpha=0.75, t0=1000000.0, weight_decay=0)
    elif coeff_opt == 'adagrad':
        opt = torch.optim.Adagrad(mr.parameters(), lr=lr, lr_decay=0, weight_decay=0, initial_accumulator_value=0)
    elif coeff_opt == 'rmsprop':
        opt = torch.optim.RMSprop(mr.parameters(), lr=lr, alpha=0.99, eps=1e-08, weight_decay=0, momentum=0,
                                  centered=False)
    elif coeff_opt == 'adam':
        opt = torch.optim.Adam(mr.parameters(), lr=lr, betas=(0.9, 0.999), eps=1e-08, weight_decay=0, amsgrad=False)
    else:
        raise RuntimeError('%s not implemented for coefficient estimation. Please check args.' % coeff_opt)
    
    for i in range(max_iter):
        opt.zero_grad()
        pred = mr(basis_pred)
        loss = loss_func(pred, target_embeddings) / 2
        loss += L1_losss_B * mr.coeff.abs().sum()

        loss.backward()
        opt.step()
        mr.compute_coeff_pos()
    
    return mr.coeff.detach()


def estimate_coeff_mat_batch(target_embeddings, basis_pred, L1_losss_B, device, max_iter = 100):
    def update_B_from_AC(AT,BT,CT,A,lr):
        BT_grad = torch.bmm( torch.bmm(BT, AT) - CT, A )
        BT = BT - lr * (BT_grad + L1_losss_B)

        BT_nonneg = BT.clamp(0,1)
        return BT_nonneg, BT_grad

    batch_size = target_embeddings.size(0)

    A = basis_pred.permute(0,2,1)

    coeff_mat_prev = torch.randn(batch_size, target_embeddings.size(1), basis_pred.size(1), requires_grad= False, device=device )
    lr = 0.05
    for i in range(max_iter):
        coeff_mat, coeff_mat_grad = update_B_from_AC(basis_pred, coeff_mat_prev, target_embeddings, A, lr)
        coeff_mat_prev = coeff_mat
    return coeff_mat

def target_emb_preparation(target_index, embeddings, n_batch, n_set, rotate_shift, target_linear_layer):
    target_embeddings = embeddings[target_index,:]
    if target_linear_layer is not None:
        target_embeddings = torch.bmm(target_embeddings, target_linear_layer.expand(target_embeddings.size(0), target_linear_layer.size(0), target_linear_layer.size(1)))
    #target_embeddings should have dimension (n_batch, n_set, n_emb_size)
    #should be the same as embeddings.select(0,target_set) and select should not copy the data
    target_embeddings = target_embeddings / (0.000000000001 + target_embeddings.norm(dim = 2, keepdim=True) ) # If this step is really slow, consider to do normalization before doing unfold
    
    #target_embeddings_4d = target_embeddings.view(-1,n_batch, n_set, target_embeddings.size(2))
    target_embeddings_rotate = torch.cat( (target_embeddings[rotate_shift:,:,:], target_embeddings[:rotate_shift,:,:]), dim = 0) if rotate_shift is not None else None
    #target_emb_neg = target_embeddings_rotate.view(-1,n_set, target_embeddings.size(2))

    #return target_embeddings, target_emb_neg
    return target_embeddings, target_embeddings_rotate

def compute_loss_set(output_emb, basis_pred, coeff_pred, entpair_embs, target_set, L1_losss_B, device, entpair_freq, coeff_opt, compute_target_grad, coeff_opt_algo, loss_type, kb_marker, num_basis, n_basis, n_basis_kb, target_linear_layer=None, pre_avg=False):

    #basis_pred should have dimension ( n_batch, n_basis, n_emb_size)
    #target_set should have dimension (n_batch, n_set)

    n_set = target_set.size(1)
    n_batch = target_set.size(0)

    # Mask out the targets and the basis preds
    device=basis_pred.device
    max_basis = max(n_basis, n_basis_kb)
    if num_basis is not None and len(num_basis) != 0:
        # Add 1 to every element to avoid 0 basis
        num_basis = num_basis + 1
        # Make sure pattern basis and kb basis are clamped to the maximum values provided
        num_basis = torch.where(kb_marker, num_basis.clamp(max=n_basis_kb), num_basis.clamp(max=n_basis))
        # Create the mask: (N, T)
        mask = (torch.arange(max_basis).expand(n_batch, -1).to(dtype=num_basis.dtype, device=num_basis.device) < num_basis.view(-1 ,1)) \
            .to(dtype=num_basis.dtype, device=num_basis.device)
    elif kb_marker is not None and len(kb_marker) != 0:
        mask = torch.where(kb_marker.unsqueeze(-1),
                           (torch.arange(max_basis) < n_basis_kb).to(dtype=torch.long, device=device),
                           (torch.arange(max_basis) < n_basis).to(dtype=torch.long, device=device))
    else:
        mask = torch.ones(basis_pred.shape[:-1]).to(dtype=basis_pred.dtype, device=basis_pred.device)

    mask = mask.unsqueeze(-1)
    basis_pred = mask.to(basis_pred.dtype) * basis_pred

    rotate_shift = random.randint(1,n_batch-1)
    if compute_target_grad:
        target_embeddings, target_emb_neg = target_emb_preparation(target_set, entpair_embs, n_batch, n_set, rotate_shift, target_linear_layer)
    else:
        with torch.no_grad():
            target_embeddings, target_emb_neg = target_emb_preparation(target_set, entpair_embs, n_batch, n_set, rotate_shift, target_linear_layer)

    with torch.no_grad():
        target_freq = entpair_freq[target_set]
        target_freq_inv = 1 / target_freq
        target_freq_inv[target_freq_inv<0] = 0 #handle null case
        inv_mean = torch.sum(target_freq_inv) / torch.sum(target_freq_inv>0).float()
        assert not torch.isnan(inv_mean), "inv_mean is nan: target_freq_inv = \n{}, \ntarget_set = \n{}".format(target_freq_inv, target_set)
        if inv_mean > 0:
            target_freq_inv_norm =  target_freq_inv / inv_mean
        else:
            target_freq_inv_norm =  target_freq_inv

        target_freq_inv_norm_neg = torch.cat( (target_freq_inv_norm[rotate_shift:,:], target_freq_inv_norm[:rotate_shift,:]), dim = 0)

        # Used for the autoencoder loss computation;
        # Average the word embeddings of the pattern/relation
        if pre_avg:
            if compute_target_grad:
                with torch.enable_grad():
                    target_embeddings = ((target_embeddings * target_freq_inv_norm.unsqueeze(dim=-1)).sum(dim=1) / (
                                0.000000000001 + target_freq_inv_norm.sum(dim=1).unsqueeze(dim=-1))).unsqueeze(dim=1)
                    target_emb_neg = ((target_emb_neg * target_freq_inv_norm_neg.unsqueeze(dim=-1)).sum(dim=1) /
                                      (0.000000000001 + target_freq_inv_norm_neg.sum(dim=1).unsqueeze(dim=-1))).unsqueeze(dim=1)
                    target_freq_inv_norm = 1
                    target_freq_inv_norm_neg = 1
            else:
                target_embeddings = ((target_embeddings * target_freq_inv_norm.unsqueeze(dim=-1)).sum(dim=1) / (
                        0.000000000001 + target_freq_inv_norm.sum(dim=1).unsqueeze(dim=-1))).unsqueeze(dim=1)
                target_emb_neg = ((target_emb_neg * target_freq_inv_norm_neg.unsqueeze(dim=-1)).sum(dim=1) /
                                  (0.000000000001 + target_freq_inv_norm_neg.sum(dim=1).unsqueeze(dim=-1))).unsqueeze(
                    dim=1)
                target_freq_inv_norm = 1
                target_freq_inv_norm_neg = 1

        if coeff_opt == 'lc':
            if coeff_opt_algo == 'sgd_bmm':
                coeff_mat = estimate_coeff_mat_batch(target_embeddings.detach(), basis_pred.detach(), L1_losss_B, device)
                coeff_mat_neg = estimate_coeff_mat_batch(target_emb_neg.detach(), basis_pred.detach(), L1_losss_B, device)
            else:
                lr_coeff = 0.05
                iter_coeff = 60
                with torch.enable_grad():
                    coeff_mat = estimate_coeff_mat_batch_opt(target_embeddings.detach(), basis_pred.detach(), L1_losss_B, device, coeff_opt_algo, lr_coeff, iter_coeff)
                    coeff_mat_neg = estimate_coeff_mat_batch_opt(target_emb_neg.detach(), basis_pred.detach(), L1_losss_B, device, coeff_opt_algo, lr_coeff, iter_coeff)
        else:
            coeff_mat = estimate_coeff_mat_batch_max(target_embeddings.detach(), basis_pred.detach(), device)
            coeff_mat_neg = estimate_coeff_mat_batch_max(target_emb_neg.detach(), basis_pred.detach(), device)
    with torch.no_grad():
        coeff_sum_basis = coeff_mat.sum(dim = 1)
        coeff_sum_basis_neg = coeff_mat_neg.sum(dim = 1)
        coeff_mean = (coeff_sum_basis.mean() + coeff_sum_basis_neg.mean()) / 2

    pred_embeddings = torch.bmm(coeff_mat, basis_pred)
    pred_embeddings_neg = torch.bmm(coeff_mat_neg, basis_pred)
    #pred_embeddings should have dimension (n_batch, n_set, n_emb_size)

    if loss_type == 'bpr':
        loss_set = target_freq_inv_norm * torch.pow( torch.norm( pred_embeddings - target_embeddings, dim = 2 ), 2)
        loss_set_neg = target_freq_inv_norm_neg * torch.pow( torch.norm( pred_embeddings_neg - target_emb_neg, dim = 2 ), 2)
    else:
        loss_set = torch.mean( target_freq_inv_norm * torch.pow( torch.norm( pred_embeddings - target_embeddings, dim = 2 ), 2) )
        loss_set_neg = - torch.mean( target_freq_inv_norm_neg * torch.pow( torch.norm( pred_embeddings_neg - target_emb_neg, dim = 2 ), 2) )
    loss_coeff_pred = torch.mean( torch.pow( coeff_sum_basis/coeff_mean - coeff_pred[:,:,0].view_as(coeff_sum_basis), 2 ) )
    loss_coeff_pred += torch.mean( torch.pow( coeff_sum_basis_neg/coeff_mean - coeff_pred[:,:,1].view_as(coeff_sum_basis_neg), 2 ) )

    if torch.isnan(loss_set).any():
        print("output_embeddings", output_emb.norm(dim = 1))
        print("basis_pred", basis_pred.norm(dim = 2))
        print("coeff_sum_basis", coeff_sum_basis)
        print("pred_embeddings", pred_embeddings.norm(dim = 2) )
        print("target_embeddings", target_embeddings.norm(dim = 2) )

    basis_pred_n = basis_pred.norm(dim = 2, keepdim=True).expand(basis_pred.shape)
    basis_pred_norm = torch.where(basis_pred_n == 0, torch.tensor(0.0, device=basis_pred.device), basis_pred / basis_pred_n)

    with torch.no_grad():
        basis_pred_sum = basis_pred_norm.sum(dim = 0, keepdim = True)
        basis_pred_count = torch.sum(mask, dim=0, keepdim=True).to(dtype=basis_pred_sum.dtype).expand(basis_pred_sum.shape)
        pred_mean = torch.where(basis_pred_count == 0, torch.tensor(0.0, device=basis_pred_sum.device), basis_pred_sum / basis_pred_count)
        loss_set_reg = - torch.sum( ((basis_pred_norm - pred_mean) * mask).norm(dim = 2) ) / torch.sum(mask)
    
    pred_mean = basis_pred_norm.sum(dim = 1, keepdim = True) / torch.sum(mask, dim=1, keepdim=True).to(device=basis_pred_norm.device)
    loss_set_div = - torch.sum( ((basis_pred_norm - pred_mean) * mask).norm(dim = 2) ) / torch.sum(mask)

    return loss_set, loss_set_reg, loss_set_div, loss_set_neg, loss_coeff_pred
