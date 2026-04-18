use anchor_lang::prelude::*;

declare_id!("ThResH1...9zQ2"); // Placeholder for deployment

#[program]
pub mod threshold_fund {
    use super::*;

    pub fn initialize_round(
        ctx: Context<InitializeRound>,
        region_id: String,
        target_amount: u64,
        deadline: i64,
        charity_wallets: Vec<Pubkey>,
        _tranche_percentages: [u8; 3]
    ) -> Result<()> {
        let round = &mut ctx.accounts.funding_round;
        round.region_id = region_id;
        round.target_amount = target_amount;
        round.raised_amount = 0;
        round.deadline = deadline;
        round.charity_wallets = charity_wallets;
        round.status = RoundStatus::Open;
        round.tranche_released = [false; 3];
        Ok(())
    }

    pub fn record_contribution(
        ctx: Context<RecordContribution>,
        amount: u64,
        donor_hash: [u8; 32]
    ) -> Result<()> {
        let round = &mut ctx.accounts.funding_round;
        round.raised_amount = round.raised_amount.checked_add(amount).unwrap();
        
        let contribution = &mut ctx.accounts.contribution;
        contribution.round = round.key();
        contribution.amount = amount;
        contribution.donor_hash = donor_hash;
        let clock = Clock::get()?;
        contribution.timestamp = clock.unix_timestamp;
        
        if round.raised_amount >= round.target_amount {
            round.status = RoundStatus::Funded;
        }
        
        Ok(())
    }

    pub fn disburse_tranche(
        ctx: Context<DisburseTranche>,
        tranche_index: u8,
        _amount: u64,
        _progress_report_hash: [u8; 32]
    ) -> Result<()> {
        let round = &mut ctx.accounts.funding_round;
        require!(tranche_index < 3, ErrorCode::InvalidTranche);
        require!(!round.tranche_released[tranche_index as usize], ErrorCode::TrancheAlreadyReleased);
        
        // In real impl, handle SPL token transfer here
        round.tranche_released[tranche_index as usize] = true;
        round.status = RoundStatus::Deploying;
        
        Ok(())
    }

    pub fn record_impact(
        ctx: Context<RecordImpact>,
        pre_score: u8,
        post_score: u8,
        _measurement_date: i64
    ) -> Result<()> {
        let round = &mut ctx.accounts.funding_round;
        round.pre_score = pre_score;
        round.post_score = post_score;
        round.status = RoundStatus::Complete;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct InitializeRound<'info> {
    #[account(init, payer = user, space = 8 + 500)]
    pub funding_round: Account<'info, FundingRound>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct RecordContribution<'info> {
    #[account(mut)]
    pub funding_round: Account<'info, FundingRound>,
    #[account(init, payer = user, space = 8 + 100)]
    pub contribution: Account<'info, Contribution>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct DisburseTranche<'info> {
    #[account(mut)]
    pub funding_round: Account<'info, FundingRound>,
    #[account(mut)]
    pub charity_wallet: SystemAccount<'info>,
}

#[derive(Accounts)]
pub struct RecordImpact<'info> {
    #[account(mut)]
    pub funding_round: Account<'info, FundingRound>,
}

#[account]
pub struct FundingRound {
    pub region_id: String,
    pub target_amount: u64,
    pub raised_amount: u64,
    pub deadline: i64,
    pub status: RoundStatus,
    pub charity_wallets: Vec<Pubkey>,
    pub tranche_released: [bool; 3],
    pub pre_score: u8,
    pub post_score: u8,
}

#[account]
pub struct Contribution {
    pub round: Pubkey,
    pub amount: u64,
    pub donor_hash: [u8; 32],
    pub timestamp: i64,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq)]
pub enum RoundStatus {
    Open,
    Funded,
    Deploying,
    Complete,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Invalid tranche index.")]
    InvalidTranche,
    #[msg("Tranche already released.")]
    TrancheAlreadyReleased,
}
