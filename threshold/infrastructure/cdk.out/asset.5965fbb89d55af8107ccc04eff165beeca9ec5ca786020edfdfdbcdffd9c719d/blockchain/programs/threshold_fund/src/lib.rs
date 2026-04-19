use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWxTWqkZUNkqYt6M8oR9P4K6qS11");

const ROUND_SEED: &[u8] = b"round";
const CONTRIBUTION_SEED: &[u8] = b"contribution";
const IMPACT_HASH_LEN: usize = 64;
const MAX_REGION_ID_LEN: usize = 32;
const MAX_CHARITIES: usize = 8;

#[program]
pub mod threshold_fund {
    use super::*;

    pub fn initialize_round(
        ctx: Context<InitializeRound>,
        round_id: u64,
        region_id: String,
        target_amount: u64,
        deadline: i64,
        charity_wallets: Vec<Pubkey>,
        tranche_percentages: [u8; 3],
    ) -> Result<()> {
        require!(region_id.len() <= MAX_REGION_ID_LEN, ErrorCode::RegionIdTooLong);
        require!(charity_wallets.len() <= MAX_CHARITIES, ErrorCode::TooManyCharities);
        require!(
            tranche_percentages.iter().copied().map(u16::from).sum::<u16>() == 100,
            ErrorCode::InvalidTrancheConfiguration
        );

        let round = &mut ctx.accounts.funding_round;
        round.bump = ctx.bumps.funding_round;
        round.round_id = round_id;
        round.region_id = region_id;
        round.authority = ctx.accounts.authority.key();
        round.target_amount = target_amount;
        round.raised_amount = 0;
        round.deadline = deadline;
        round.charity_wallets = charity_wallets;
        round.tranche_percentages = tranche_percentages;
        round.tranche_released = [false; 3];
        round.progress_report_hash = None;
        round.pre_score = None;
        round.post_score = None;
        round.status = RoundStatus::Open;
        Ok(())
    }

    pub fn record_contribution(
        ctx: Context<RecordContribution>,
        contribution_id: u64,
        amount: u64,
        donor_hash: [u8; 32],
    ) -> Result<()> {
        require!(amount > 0, ErrorCode::InvalidAmount);

        let round = &mut ctx.accounts.funding_round;
        require!(round.status != RoundStatus::Closed, ErrorCode::RoundClosed);

        round.raised_amount = round
            .raised_amount
            .checked_add(amount)
            .ok_or(ErrorCode::ArithmeticOverflow)?;

        if round.raised_amount >= round.target_amount {
            round.status = RoundStatus::Funded;
        }

        let contribution = &mut ctx.accounts.contribution;
        contribution.bump = ctx.bumps.contribution;
        contribution.contribution_id = contribution_id;
        contribution.round = round.key();
        contribution.amount = amount;
        contribution.donor_hash = donor_hash;
        contribution.timestamp = Clock::get()?.unix_timestamp;
        Ok(())
    }

    pub fn submit_progress_report(
        ctx: Context<SubmitProgressReport>,
        progress_report_hash: String,
    ) -> Result<()> {
        require!(
            !progress_report_hash.is_empty() && progress_report_hash.len() <= IMPACT_HASH_LEN,
            ErrorCode::InvalidProgressReportHash
        );

        let round = &mut ctx.accounts.funding_round;
        round.progress_report_hash = Some(progress_report_hash);
        Ok(())
    }

    pub fn disburse_tranche(ctx: Context<DisburseTranche>, tranche_index: u8) -> Result<()> {
        let round = &mut ctx.accounts.funding_round;
        require!(tranche_index < 3, ErrorCode::InvalidTranche);
        require!(
            !round.tranche_released[tranche_index as usize],
            ErrorCode::TrancheAlreadyReleased
        );

        if tranche_index == 1 || tranche_index == 2 {
            require!(
                round.progress_report_hash.is_some(),
                ErrorCode::MissingProgressReport
            );
        }

        round.tranche_released[tranche_index as usize] = true;
        round.status = if tranche_index == 2 {
            RoundStatus::Closed
        } else {
            RoundStatus::Deploying
        };
        Ok(())
    }

    pub fn record_impact(
        ctx: Context<RecordImpact>,
        pre_score: u8,
        post_score: u8,
    ) -> Result<()> {
        let round = &mut ctx.accounts.funding_round;
        round.pre_score = Some(pre_score);
        round.post_score = Some(post_score);
        Ok(())
    }
}

#[derive(Accounts)]
#[instruction(round_id: u64)]
pub struct InitializeRound<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + FundingRound::INIT_SPACE,
        seeds = [ROUND_SEED, authority.key().as_ref(), &round_id.to_le_bytes()],
        bump
    )]
    pub funding_round: Account<'info, FundingRound>,
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(contribution_id: u64)]
pub struct RecordContribution<'info> {
    #[account(mut, has_one = authority)]
    pub funding_round: Account<'info, FundingRound>,
    #[account(mut)]
    pub authority: Signer<'info>,
    #[account(
        init,
        payer = authority,
        space = 8 + Contribution::INIT_SPACE,
        seeds = [
            CONTRIBUTION_SEED,
            funding_round.key().as_ref(),
            &contribution_id.to_le_bytes()
        ],
        bump
    )]
    pub contribution: Account<'info, Contribution>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct SubmitProgressReport<'info> {
    #[account(mut, has_one = authority)]
    pub funding_round: Account<'info, FundingRound>,
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct DisburseTranche<'info> {
    #[account(mut, has_one = authority)]
    pub funding_round: Account<'info, FundingRound>,
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct RecordImpact<'info> {
    #[account(mut, has_one = authority)]
    pub funding_round: Account<'info, FundingRound>,
    pub authority: Signer<'info>,
}

#[account]
#[derive(InitSpace)]
pub struct FundingRound {
    pub bump: u8,
    pub round_id: u64,
    #[max_len(MAX_REGION_ID_LEN)]
    pub region_id: String,
    pub authority: Pubkey,
    pub target_amount: u64,
    pub raised_amount: u64,
    pub deadline: i64,
    pub status: RoundStatus,
    #[max_len(MAX_CHARITIES)]
    pub charity_wallets: Vec<Pubkey>,
    pub tranche_percentages: [u8; 3],
    pub tranche_released: [bool; 3],
    #[max_len(IMPACT_HASH_LEN)]
    pub progress_report_hash: Option<String>,
    pub pre_score: Option<u8>,
    pub post_score: Option<u8>,
}

#[account]
#[derive(InitSpace)]
pub struct Contribution {
    pub bump: u8,
    pub contribution_id: u64,
    pub round: Pubkey,
    pub amount: u64,
    pub donor_hash: [u8; 32],
    pub timestamp: i64,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace)]
pub enum RoundStatus {
    Open,
    Funded,
    Deploying,
    Closed,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Invalid tranche index.")]
    InvalidTranche,
    #[msg("Tranche already released.")]
    TrancheAlreadyReleased,
    #[msg("A progress report is required before this tranche can be released.")]
    MissingProgressReport,
    #[msg("The progress report hash is invalid.")]
    InvalidProgressReportHash,
    #[msg("Tranche percentages must sum to 100.")]
    InvalidTrancheConfiguration,
    #[msg("The round amount must be greater than zero.")]
    InvalidAmount,
    #[msg("Arithmetic overflow while updating balances.")]
    ArithmeticOverflow,
    #[msg("This round is already closed.")]
    RoundClosed,
    #[msg("The region id exceeds the supported length.")]
    RegionIdTooLong,
    #[msg("Too many charity wallets were provided.")]
    TooManyCharities,
}
